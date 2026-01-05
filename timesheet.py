from flask import Flask, render_template_string, jsonify, request
import json
import os
from datetime import datetime

app = Flask(__name__)

DB_FILE = 'timesheets_database.json'

def get_database():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return []

def save_database(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=2)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Consulting Timesheet</title>
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
            <h1 class="text-3xl font-bold text-gray-800 mb-6">Consulting Timesheet</h1>
            
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
                        <!-- Rows will be added here -->
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

    <!-- Modal for viewing saved timesheets -->
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

        async function saveTimesheet() {
            const consultant = document.getElementById('consultant').value;
            const client = document.getElementById('client').value;
            const period = document.getElementById('period').value;
            const rate = document.getElementById('rate').value;

            if (!consultant || !client || !period) {
                alert('Please fill in Consultant Name, Client Name, and Period before saving.');
                return;
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
                return;
            }

            const timesheet = {
                id: Date.now(),
                savedDate: new Date().toISOString(),
                consultant: consultant,
                client: client,
                period: period,
                rate: parseFloat(rate) || 0,
                entries: entries,
                totalHours: parseFloat(document.getElementById('total-hours').textContent),
                totalAmount: rate ? parseFloat(document.getElementById('total-hours').textContent) * parseFloat(rate) : 0
            };

            try {
                const response = await fetch('/api/timesheets', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(timesheet)
                });
                
                if (response.ok) {
                    alert('Timesheet saved successfully to timesheets_database.json!');
                } else {
                    alert('Error saving timesheet');
                }
            } catch (error) {
                alert('Error saving timesheet: ' + error.message);
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
                                    '<button onclick="loadTimesheet(' + index + ')" class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">Load</button>' +
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

        async function loadTimesheet(index) {
            try {
                const response = await fetch('/api/timesheets');
                const db = await response.json();
                const timesheet = db[index];
                
                document.getElementById('consultant').value = timesheet.consultant;
                document.getElementById('client').value = timesheet.client;
                document.getElementById('period').value = timesheet.period;
                document.getElementById('rate').value = timesheet.rate;
                
                // Clear existing entries
                document.getElementById('entries-tbody').innerHTML = '';
                entryId = 0;
                
                // Load entries
                timesheet.entries.forEach(function(entry) {
                    addEntry();
                    const row = document.getElementById('entry-' + entryId);
                    row.querySelector('.entry-date').value = entry.date;
                    row.querySelector('.entry-project').value = entry.project;
                    row.querySelector('.entry-description').value = entry.description;
                    row.querySelector('.entry-hours').value = entry.hours;
                });
                
                calculateTotals();
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

        function handlePrint() {
            setTimeout(function() {
                window.print();
            }, 100);
        }

        // Add initial entry
        addEntry();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/timesheets', methods=['GET'])
def get_timesheets():
    return jsonify(get_database())

@app.route('/api/timesheets', methods=['POST'])
def save_timesheet():
    timesheet = request.json
    db = get_database()
    db.append(timesheet)
    save_database(db)
    return jsonify({'success': True})

@app.route('/api/timesheets/<int:timesheet_id>', methods=['DELETE'])
def delete_timesheet(timesheet_id):
    db = get_database()
    db = [t for t in db if t['id'] != timesheet_id]
    save_database(db)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)