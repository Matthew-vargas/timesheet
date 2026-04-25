from flask import Flask, render_template_string, jsonify, request, session, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# On Render, store the database on the persistent disk outside the source tree
# so redeploys don't overwrite production data. Locally, use the current directory.
if os.environ.get('RENDER'):
    DB_FILE = '/opt/render/project/data/timesheets_database.json'
else:
    DB_FILE = 'timesheets_database.json'

def setup_database_path():
    """Ensure the data directory exists and migrate existing data if needed."""
    data_dir = os.path.dirname(DB_FILE)
    if data_dir:
        os.makedirs(data_dir, exist_ok=True)

    # If no database exists at the target path yet, check if there's existing
    # data at the old source-tree path and migrate it over automatically.
    if not os.path.exists(DB_FILE):
        old_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'timesheets_database.json')
        if os.path.exists(old_path) and old_path != os.path.abspath(DB_FILE):
            try:
                import shutil
                shutil.copy2(old_path, DB_FILE)
                print(f"Migrated existing database from {old_path} to {DB_FILE}")
            except (IOError, OSError) as e:
                print(f"Migration copy failed: {e}")

    # If still no file (first boot with no prior data), seed an empty database.
    if not os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'w') as f:
                json.dump({"Matthew": [], "Joan": []}, f, indent=2)
            print(f"Created fresh database at {DB_FILE}")
        except IOError as e:
            print(f"Error creating database: {e}")

setup_database_path()

def get_database():
    """Load the entire database structure"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "Matthew": [],
        "Joan": []
    }

def get_user_timesheets(user):
    """Get timesheets for a specific user"""
    db = get_database()
    return db.get(user, [])

def save_user_timesheets(user, timesheets):
    """Save timesheets for a specific user"""
    db = get_database()
    db[user] = timesheets
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(db, f, indent=2)
    except IOError as e:
        print(f"Error saving database: {e}")

def migrate_database():
    """Migrate old flat array database to user-separated structure"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                print("Migrating database to user-separated format...")
                new_db = {
                    "Matthew": data,
                    "Joan": []
                }
                with open(DB_FILE, 'w') as f:
                    json.dump(new_db, f, indent=2)
                print("Migration complete!")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Migration error: {e}")

migrate_database()

USER_SELECTION_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Select User - Timesheet</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen flex items-center justify-center">
    <div class="bg-white rounded-lg shadow-xl p-12 max-w-md w-full">
        <h1 class="text-4xl font-bold text-gray-800 mb-2 text-center">Timesheet App</h1>
        <p class="text-gray-600 text-center mb-8">Select your user profile</p>
        
        <div class="space-y-4">
            <form action="/select-user" method="POST">
                <input type="hidden" name="user" value="Matthew">
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-6 rounded-lg transition-colors shadow-md hover:shadow-lg transform hover:scale-105 duration-200">
                    <div class="flex items-center justify-center gap-3">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                        </svg>
                        <span class="text-xl">Matthew</span>
                    </div>
                </button>
            </form>
            
            <form action="/select-user" method="POST">
                <input type="hidden" name="user" value="Joan">
                <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-4 px-6 rounded-lg transition-colors shadow-md hover:shadow-lg transform hover:scale-105 duration-200">
                    <div class="flex items-center justify-center gap-3">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                        </svg>
                        <span class="text-xl">Joan</span>
                    </div>
                </button>
            </form>
        </div>
    </div>
</body>
</html>
"""

TIMESHEET_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Consulting Timesheet - {{ current_user }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @media print {
            .no-print { display: none !important; }
            body { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
        }
    </style>
</head>
<body class="bg-gray-50">
    <div class="max-w-6xl mx-auto p-8 bg-white" id="timesheet">
        <div class="mb-8">
            <div class="flex justify-between items-center mb-6">
                <h1 class="text-3xl font-bold text-gray-800">Consulting Timesheet</h1>
                <div class="flex items-center gap-4 no-print">
                    <div class="bg-blue-100 text-blue-800 px-4 py-2 rounded-lg font-semibold">
                        <svg class="w-5 h-5 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                        </svg>
                        {{ current_user }}
                    </div>
                    <a href="/switch-user" class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors text-sm">
                        Switch User
                    </a>
                </div>
            </div>
            
            <div class="grid grid-cols-2 gap-6 mb-6">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Consultant Name
                    </label>
                    <input
                        type="text"
                        id="consultant"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Your name"
                        value="{{ current_user }}"
                    />
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Client Name
                    </label>
                    <input
                        type="text"
                        id="client"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Client name"
                    />
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Period
                    </label>
                    <input
                        type="text"
                        id="period"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="e.g., Dec 1-15, 2024"
                    />
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Hourly Rate ($)
                    </label>
                    <input
                        type="number"
                        id="rate"
                        class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="150.00"
                        step="0.01"
                        oninput="calculateTotals()"
                    />
                </div>
            </div>
        </div>

        <div class="mb-6">
            <div class="overflow-x-auto">
                <table class="w-full border-collapse">
                    <thead>
                        <tr class="bg-gray-100">
                            <th class="border border-gray-300 px-4 py-3 text-left text-sm font-semibold text-gray-700">
                                Date
                            </th>
                            <th class="border border-gray-300 px-4 py-3 text-left text-sm font-semibold text-gray-700">
                                Project/Task
                            </th>
                            <th class="border border-gray-300 px-4 py-3 text-left text-sm font-semibold text-gray-700">
                                Description
                            </th>
                            <th class="border border-gray-300 px-4 py-3 text-left text-sm font-semibold text-gray-700">
                                Hours
                            </th>
                            <th class="border border-gray-300 px-4 py-3 text-center text-sm font-semibold text-gray-700 no-print">
                                Action
                            </th>
                        </tr>
                    </thead>
                    <tbody id="entries-tbody">
                    </tbody>
                </table>
            </div>
            
            <button
                onclick="addEntry()"
                class="mt-4 flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors no-print"
            >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                </svg>
                Add Row
            </button>
        </div>

        <div class="border-t-2 border-gray-300 pt-4">
            <div class="flex justify-end">
                <div class="w-80">
                    <div class="flex justify-between items-center mb-2 pb-2">
                        <span class="text-lg font-semibold text-gray-700">Total Hours:</span>
                        <span class="text-2xl font-bold text-gray-900" id="total-hours">0.00</span>
                    </div>
                    <div class="flex justify-between items-center pt-2 border-t border-gray-300" id="total-amount-row" style="display: none;">
                        <span class="text-lg font-semibold text-gray-700">Total Amount:</span>
                        <span class="text-2xl font-bold text-green-700" id="total-amount">$0.00</span>
                    </div>
                </div>
            </div>
        </div>

        <div id="editing-banner" class="hidden mb-4 px-4 py-2 bg-yellow-50 border border-yellow-300 rounded-md text-yellow-800 text-sm font-medium no-print">
            ✏️ Editing existing timesheet — <strong>Save Timesheet</strong> will overwrite it, or use <strong>Save as New</strong> to create a copy.
        </div>

        <div class="mt-8 flex gap-4 no-print flex-wrap">
            <button
                onclick="saveTimesheet()"
                class="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
            >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path>
                </svg>
                Save Timesheet
            </button>

            <button
                id="save-as-new-btn"
                onclick="saveAsNew()"
                class="hidden flex items-center gap-2 px-6 py-3 bg-orange-500 text-white rounded-md hover:bg-orange-600 transition-colors font-medium"
            >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2"></path>
                </svg>
                Save as New
            </button>
            
            <button
                onclick="handlePrint()"
                class="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors font-medium"
            >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
                </svg>
                Print / Save as PDF
            </button>
            
            <button
                onclick="showSavedTimesheets()"
                class="flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors font-medium"
            >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                View Saved Timesheets
            </button>
        </div>

        <div class="mt-8 pt-6 border-t border-gray-300">
            <p class="text-sm text-gray-600 mb-4">Consultant Signature: ___________________________ Date: ___________</p>
            <p class="text-sm text-gray-600">Client Approval: ___________________________ Date: ___________</p>
        </div>
    </div>

    <div id="modal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50 no-print" onclick="closeModal(event)">
        <div class="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto" onclick="event.stopPropagation()">
            <div class="flex justify-between items-center mb-4">
                <h2 class="text-2xl font-bold text-gray-800">Saved Timesheets</h2>
                <button onclick="closeModal()" class="text-gray-600 hover:text-gray-800">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
            <div id="saved-timesheets-list"></div>
        </div>
    </div>

    <script>
        let entryId = 0;
        let currentTimesheetId = null;

        function addEntry() {
            entryId++;
            const tbody = document.getElementById('entries-tbody');
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-50';
            row.id = 'entry-' + entryId;
            row.innerHTML = 
                '<td class="border border-gray-300 px-2 py-2">' +
                    '<input type="date" class="entry-date w-full px-2 py-1 border-0 focus:outline-none focus:ring-1 focus:ring-blue-500 rounded" />' +
                '</td>' +
                '<td class="border border-gray-300 px-2 py-2">' +
                    '<input type="text" class="entry-project w-full px-2 py-1 border-0 focus:outline-none focus:ring-1 focus:ring-blue-500 rounded" placeholder="Project name" />' +
                '</td>' +
                '<td class="border border-gray-300 px-2 py-2">' +
                    '<textarea class="entry-description w-full px-2 py-1 border-0 focus:outline-none focus:ring-1 focus:ring-blue-500 rounded resize-y min-h-[2.5rem]" placeholder="Work description" rows="2"></textarea>' +
                '</td>' +
                '<td class="border border-gray-300 px-2 py-2">' +
                    '<input type="number" class="hours-input entry-hours w-full px-2 py-1 border-0 focus:outline-none focus:ring-1 focus:ring-blue-500 rounded" placeholder="0.0" step="0.25" min="0" oninput="calculateTotals()" />' +
                '</td>' +
                '<td class="border border-gray-300 px-2 py-2 text-center no-print">' +
                    '<button onclick="removeEntry(' + entryId + ')" class="text-red-600 hover:text-red-800 p-1">' +
                        '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">' +
                            '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>' +
                        '</svg>' +
                    '</button>' +
                '</td>';
            tbody.appendChild(row);
        }

        function removeEntry(id) {
            const row = document.getElementById('entry-' + id);
            if (row) {
                row.remove();
                calculateTotals();
            }
        }

        function calculateTotals() {
            const hoursInputs = document.querySelectorAll('.hours-input');
            let totalHours = 0;
            
            hoursInputs.forEach(function(input) {
                const value = parseFloat(input.value) || 0;
                totalHours += value;
            });
            
            document.getElementById('total-hours').textContent = totalHours.toFixed(2);
            
            const rate = parseFloat(document.getElementById('rate').value) || 0;
            if (rate > 0) {
                const totalAmount = totalHours * rate;
                document.getElementById('total-amount').textContent = '$' + totalAmount.toFixed(2);
                document.getElementById('total-amount-row').style.display = 'flex';
            } else {
                document.getElementById('total-amount-row').style.display = 'none';
            }
        }

        function buildTimesheetPayload(overrideId) {
            const consultant = document.getElementById('consultant').value;
            const client = document.getElementById('client').value;
            const period = document.getElementById('period').value;
            const rate = document.getElementById('rate').value;

            if (!consultant || !client || !period) {
                alert('Please fill in Consultant Name, Client Name, and Period before saving.');
                return null;
            }

            const entries = [];
            const rows = document.querySelectorAll('#entries-tbody tr');
            rows.forEach(function(row) {
                const date = row.querySelector('.entry-date').value;
                const project = row.querySelector('.entry-project').value;
                const description = row.querySelector('.entry-description').value;
                const hours = row.querySelector('.entry-hours').value;
                if (date || project || description || hours) {
                    entries.push({
                        date: date,
                        project: project,
                        description: description,
                        hours: parseFloat(hours) || 0
                    });
                }
            });

            if (entries.length === 0) {
                alert('Please add at least one time entry before saving.');
                return null;
            }

            const totalHours = parseFloat(document.getElementById('total-hours').textContent);
            return {
                id: overrideId !== undefined ? overrideId : Date.now(),
                savedDate: new Date().toISOString(),
                consultant: consultant,
                client: client,
                period: period,
                rate: parseFloat(rate) || 0,
                entries: entries,
                totalHours: totalHours,
                totalAmount: rate ? totalHours * parseFloat(rate) : 0
            };
        }

        async function saveTimesheet() {
            const isUpdate = currentTimesheetId !== null;
            const timesheet = buildTimesheetPayload(isUpdate ? currentTimesheetId : undefined);
            if (!timesheet) return;

            try {
                const url = isUpdate ? '/api/timesheets/' + currentTimesheetId : '/api/timesheets';
                const method = isUpdate ? 'PUT' : 'POST';

                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(timesheet)
                });

                if (response.ok) {
                    currentTimesheetId = timesheet.id;
                    alert(isUpdate ? 'Timesheet updated successfully!' : 'Timesheet saved successfully!');
                    updateEditingBanner();
                } else {
                    alert('Error saving timesheet');
                }
            } catch (error) {
                alert('Error saving timesheet: ' + error.message);
            }
        }

        async function saveAsNew() {
            const timesheet = buildTimesheetPayload();  // always generates a fresh Date.now() id
            if (!timesheet) return;

            try {
                const response = await fetch('/api/timesheets', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(timesheet)
                });

                if (response.ok) {
                    currentTimesheetId = timesheet.id;
                    alert('Saved as a new timesheet!');
                    updateEditingBanner();
                } else {
                    alert('Error saving new timesheet');
                }
            } catch (error) {
                alert('Error saving new timesheet: ' + error.message);
            }
        }

        async function showSavedTimesheets() {
            try {
                const response = await fetch('/api/timesheets');
                const db = await response.json();
                const listDiv = document.getElementById('saved-timesheets-list');
                
                if (db.length === 0) {
                    listDiv.innerHTML = '<p class="text-gray-600 text-center py-8">No saved timesheets yet.</p>';
                } else {
                    let html = '<div class="space-y-4">';
                    db.forEach(function(timesheet, index) {
                        const savedDate = new Date(timesheet.savedDate).toLocaleString();
                        html += 
                            '<div class="border border-gray-300 rounded-lg p-4 hover:bg-gray-50">' +
                                '<div class="flex justify-between items-start mb-2">' +
                                    '<div>' +
                                        '<h3 class="font-semibold text-lg text-gray-800">' + timesheet.client + '</h3>' +
                                        '<p class="text-sm text-gray-600">Consultant: ' + timesheet.consultant + '</p>' +
                                        '<p class="text-sm text-gray-600">Period: ' + timesheet.period + '</p>' +
                                        '<p class="text-xs text-gray-500 mt-1">Saved: ' + savedDate + '</p>' +
                                    '</div>' +
                                    '<div class="text-right">' +
                                        '<p class="text-lg font-bold text-gray-800">' + timesheet.totalHours.toFixed(2) + ' hrs</p>' +
                                        (timesheet.totalAmount > 0 ? '<p class="text-md font-semibold text-green-700">$' + timesheet.totalAmount.toFixed(2) + '</p>' : '') +
                                    '</div>' +
                                '</div>' +
                                '<div class="flex gap-2 mt-3">' +
                                    '<button onclick="loadTimesheet(' + timesheet.id + ')" class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">Load</button>' +
                                    '<button onclick="deleteTimesheet(' + timesheet.id + ')" class="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700">Delete</button>' +
                                '</div>' +
                            '</div>';
                    });
                    html += '</div>';
                    listDiv.innerHTML = html;
                }
                
                document.getElementById('modal').classList.remove('hidden');
                document.getElementById('modal').classList.add('flex');
            } catch (error) {
                alert('Error loading timesheets: ' + error.message);
            }
        }

        async function loadTimesheet(id) {
            try {
                const response = await fetch('/api/timesheets');
                const db = await response.json();
                const timesheet = db.find(function(t) { return t.id === id; });

                if (!timesheet) {
                    alert('Could not find that timesheet.');
                    return;
                }
                
                document.getElementById('consultant').value = timesheet.consultant;
                document.getElementById('client').value = timesheet.client;
                document.getElementById('period').value = timesheet.period;
                document.getElementById('rate').value = timesheet.rate;
                
                document.getElementById('entries-tbody').innerHTML = '';
                entryId = 0;
                
                timesheet.entries.forEach(function(entry) {
                    addEntry();
                    const row = document.getElementById('entry-' + entryId);
                    row.querySelector('.entry-date').value = entry.date;
                    row.querySelector('.entry-project').value = entry.project;
                    row.querySelector('.entry-description').value = entry.description;
                    row.querySelector('.entry-hours').value = entry.hours;
                });
                
                currentTimesheetId = timesheet.id;
                calculateTotals();
                updateEditingBanner();
                closeModal();
            } catch (error) {
                alert('Error loading timesheet: ' + error.message);
            }
        }

        async function deleteTimesheet(id) {
            if (confirm('Are you sure you want to delete this timesheet?')) {
                try {
                    const response = await fetch('/api/timesheets/' + id, {
                        method: 'DELETE'
                    });
                    
                    if (response.ok) {
                        showSavedTimesheets();
                    } else {
                        alert('Error deleting timesheet');
                    }
                } catch (error) {
                    alert('Error deleting timesheet: ' + error.message);
                }
            }
        }

        function closeModal(event) {
            if (!event || event.target.id === 'modal') {
                document.getElementById('modal').classList.add('hidden');
                document.getElementById('modal').classList.remove('flex');
            }
        }

        function updateEditingBanner() {
            const banner = document.getElementById('editing-banner');
            const saveAsNewBtn = document.getElementById('save-as-new-btn');
            if (currentTimesheetId !== null) {
                banner.classList.remove('hidden');
                saveAsNewBtn.classList.remove('hidden');
            } else {
                banner.classList.add('hidden');
                saveAsNewBtn.classList.add('hidden');
            }
        }

        function handlePrint() {
            setTimeout(function() {
                window.print();
            }, 100);
        }

        addEntry();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(USER_SELECTION_TEMPLATE)

@app.route('/select-user', methods=['POST'])
def select_user():
    user = request.form.get('user')
    if user in ['Matthew', 'Joan']:
        session['user'] = user
        return redirect(url_for('timesheet'))
    return redirect(url_for('index'))

@app.route('/switch-user')
def switch_user():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/timesheet')
def timesheet():
    if 'user' not in session:
        return redirect(url_for('index'))
    return render_template_string(TIMESHEET_TEMPLATE, current_user=session['user'])

@app.route('/api/timesheets', methods=['GET'])
def get_timesheets():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = session['user']
    user_timesheets = get_user_timesheets(user)
    return jsonify(user_timesheets)

@app.route('/api/timesheets', methods=['POST'])
def save_timesheet_route():
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = session['user']
    timesheet = request.json
    
    user_timesheets = get_user_timesheets(user)
    user_timesheets.append(timesheet)
    
    save_user_timesheets(user, user_timesheets)
    
    return jsonify({'success': True})

@app.route('/api/timesheets/<int:timesheet_id>', methods=['PUT'])
def update_timesheet(timesheet_id):
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    user = session['user']
    timesheet = request.json

    user_timesheets = get_user_timesheets(user)
    for i, t in enumerate(user_timesheets):
        if t['id'] == timesheet_id:
            user_timesheets[i] = timesheet
            save_user_timesheets(user, user_timesheets)
            return jsonify({'success': True})

    return jsonify({'error': 'Timesheet not found'}), 404

@app.route('/api/timesheets/<int:timesheet_id>', methods=['DELETE'])
def delete_timesheet(timesheet_id):
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = session['user']
    
    user_timesheets = get_user_timesheets(user)
    user_timesheets = [t for t in user_timesheets if t['id'] != timesheet_id]
    
    save_user_timesheets(user, user_timesheets)
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)