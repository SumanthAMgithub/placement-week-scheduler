const API_URL = "http://127.0.0.1:8000";


// Store all schedules returned by backend
let allSchedules = [];


// Current page
let currentPage = 1;


// Number of interviews displayed per page
const ITEMS_PER_PAGE = 50;


// --------------------------------------------------
// LOAD METRICS
// --------------------------------------------------

async function loadMetrics() {

    try {

        const response = await fetch(
            `${API_URL}/schedule/metrics`
        );

        if (!response.ok) {
            throw new Error(
                `Metrics request failed: ${response.status}`
            );
        }

        const data = await response.json();


        document.getElementById(
            "totalStudents"
        ).textContent =
            data.total_students;


        document.getElementById(
            "totalShortlisted"
        ).textContent =
            data.total_shortlisted_interviews;


        document.getElementById(
            "scheduledInterviews"
        ).textContent =
            data.scheduled_interviews;


        document.getElementById(
            "unscheduledInterviews"
        ).textContent =
            data.unscheduled_interviews;


        document.getElementById(
            "schedulingRate"
        ).textContent =
            data.scheduling_rate_percent + "%";

    }

    catch (error) {

        showMessage(
            "Unable to load metrics."
        );

        console.error(error);

    }

}


// --------------------------------------------------
// LOAD SCHEDULE
// --------------------------------------------------

async function loadSchedule() {

    try {

        const response = await fetch(
            `${API_URL}/schedule/`
        );

        if (!response.ok) {
            throw new Error(
                `Schedule request failed: ${response.status}`
            );
        }

        const data = await response.json();


        allSchedules = data.schedule || [];


        currentPage = 1;


        document.getElementById(
            "scheduleCount"
        ).textContent =
            data.total_interviews +
            " interviews";


        renderSchedule();

    }

    catch (error) {

        showMessage(
            "Unable to load schedule."
        );

        console.error(error);

    }

}


// --------------------------------------------------
// RENDER CURRENT PAGE
// --------------------------------------------------

function renderSchedule() {

    const table =
        document.getElementById(
            "scheduleTable"
        );


    table.innerHTML = "";


    const totalPages =
        Math.ceil(
            allSchedules.length /
            ITEMS_PER_PAGE
        );


    if (totalPages === 0) {

        document.getElementById(
            "pageInfo"
        ).textContent =
            "Page 0 of 0";

        document.getElementById(
            "previousButton"
        ).disabled = true;

        document.getElementById(
            "nextButton"
        ).disabled = true;

        return;

    }


    // Make sure current page is valid
    if (currentPage > totalPages) {
        currentPage = totalPages;
    }


    const startIndex =
        (currentPage - 1) *
        ITEMS_PER_PAGE;


    const endIndex =
        startIndex +
        ITEMS_PER_PAGE;


    const currentSchedules =
        allSchedules.slice(
            startIndex,
            endIndex
        );


    currentSchedules.forEach(
        interview => {

            const row =
                document.createElement("tr");


            row.innerHTML = `

                <td>
                    ${interview.interview_id}
                </td>

                <td>
                    ${interview.student ?? "-"}
                </td>

                <td>
                    ${interview.company ?? "-"}
                </td>

                <td>
                    ${interview.room ?? "-"}
                </td>

                <td>
                    ${interview.panel ?? "-"}
                </td>

                <td>
                    ${interview.day ?? "-"}
                </td>

                <td>
                    ${interview.start_time ?? "-"}
                    -
                    ${interview.end_time ?? "-"}
                </td>

                <td class="status-scheduled">
                    ${interview.status}
                </td>

            `;


            table.appendChild(row);

        }
    );


    // Update pagination information

    document.getElementById(
        "pageInfo"
    ).textContent =
        `Page ${currentPage} of ${totalPages}`;


    // Enable/disable buttons

    document.getElementById(
        "previousButton"
    ).disabled =
        currentPage === 1;


    document.getElementById(
        "nextButton"
    ).disabled =
        currentPage === totalPages;

}


// --------------------------------------------------
// NEXT PAGE
// --------------------------------------------------

function nextPage() {

    const totalPages =
        Math.ceil(
            allSchedules.length /
            ITEMS_PER_PAGE
        );


    if (currentPage < totalPages) {

        currentPage++;

        renderSchedule();

    }

}


// --------------------------------------------------
// PREVIOUS PAGE
// --------------------------------------------------

function previousPage() {

    if (currentPage > 1) {

        currentPage--;

        renderSchedule();

    }

}


// --------------------------------------------------
// GENERATE SCHEDULE
// --------------------------------------------------

async function generateSchedule() {

    showMessage(
        "Generating placement schedule... Please wait."
    );


    try {

        const response = await fetch(
            `${API_URL}/schedule/generate`,
            {
                method: "POST"
            }
        );


        if (!response.ok) {

            throw new Error(
                `Generate request failed: ${response.status}`
            );

        }


        const data =
            await response.json();


        showMessage(
            `Schedule generated successfully. ` +
            `Scheduled: ${data.scheduled_count}, ` +
            `Unscheduled: ${data.unscheduled_count}`
        );


        await loadDashboard();

    }

    catch (error) {

        showMessage(
            "Failed to generate schedule."
        );

        console.error(error);

    }

}


// --------------------------------------------------
// RESET SCHEDULE
// --------------------------------------------------

async function resetSchedule() {

    const confirmed =
        confirm(
            "Are you sure you want to reset the schedule?"
        );


    if (!confirmed) {
        return;
    }


    try {

        showMessage(
            "Resetting schedule..."
        );


        const response =
            await fetch(
                `${API_URL}/schedule/reset`,
                {
                    method: "POST"
                }
            );


        if (!response.ok) {

            throw new Error(
                `Reset request failed: ${response.status}`
            );

        }


        const data =
            await response.json();


        showMessage(
            data.message +
            " Deleted: " +
            data.deleted_interviews
        );


        await loadDashboard();

    }

    catch (error) {

        showMessage(
            "Failed to reset schedule."
        );

        console.error(error);

    }

}


// --------------------------------------------------
// LOAD EVERYTHING
// --------------------------------------------------

async function loadDashboard() {

    await loadMetrics();

    await loadSchedule();

}


// --------------------------------------------------
// SYSTEM MESSAGE
// --------------------------------------------------

function showMessage(message) {

    document.getElementById(
        "message"
    ).textContent =
        message;

}


// --------------------------------------------------
// INITIAL LOAD
// --------------------------------------------------

window.onload = function () {

    loadDashboard();

};