"use strict";


const PATHS = {
    health:
        "../logs/latest_automation_health.json",

    weekly:
        "../logs/latest_weekly_automation_status.json",

    successful:
        "../logs/latest_successful_weekly_run.json",

    refresh:
        "../logs/latest_refresh_status.json",

    batch:
        "../logs/latest_batch_status.json",

    opportunities:
        "../opportunities/deduplicated_ranked_output.json"
};


let allOpportunities = [];

let favoriteIds =
    loadFavorites();


async function fetchJson(path) {

    const separator =
        path.includes("?")
            ? "&"
            : "?";

    const response =
        await fetch(
            `${path}${separator}t=${Date.now()}`,
            {
                cache: "no-store"
            }
        );

    if (!response.ok) {

        throw new Error(
            `${path} returned HTTP ${response.status}`
        );
    }

    return response.json();
}


function text(
    id,
    value,
    fallback = "unknown"
) {

    const element =
        document.getElementById(id);

    if (!element) {
        return;
    }

    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {

        element.textContent =
            fallback;

        return;
    }

    element.textContent =
        String(value);
}


function firstDefined(
    ...values
) {

    for (const value of values) {

        if (
            value !== undefined &&
            value !== null &&
            value !== ""
        ) {

            return value;
        }
    }

    return null;
}


function formatDateTime(value) {

    if (!value) {
        return "unknown";
    }

    const normalized =
        String(value).replace(
            " ",
            "T"
        );

    const date =
        new Date(normalized);

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return value;
    }

    return date.toLocaleString(
        "en-NZ"
    );
}


function formatDuration(seconds) {

    const value =
        Number(seconds);

    if (
        !Number.isFinite(value) ||
        value < 0
    ) {

        return "unknown";
    }

    const total =
        Math.round(value);

    const minutes =
        Math.floor(
            total / 60
        );

    const remainingSeconds =
        total % 60;

    if (minutes === 0) {

        return `${remainingSeconds}s`;
    }

    return (
        `${minutes}m ${remainingSeconds}s`
    );
}


function fileNameFromPath(value) {

    if (!value) {
        return "unavailable";
    }

    const normalized =
        String(value).replace(
            /\\/g,
            "/"
        );

    const pieces =
        normalized.split("/");

    return pieces[
        pieces.length - 1
    ];
}


function escapeHtml(value) {

    return String(
        value ?? ""
    )
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );
}


/* ============================================================
   Demo Mode
============================================================ */


function renderDemoMode(
    weekly
) {

    const demoMode =
        weekly?.demo_mode === true;


    const demoModeBanner =
        document.getElementById(
            "demoModeBanner"
        );


    const dataSourceLabel =
        document.getElementById(
            "dataSourceLabel"
        );


    const backendDataBanner =
        document.getElementById(
            "backendDataBanner"
        );


    if (demoModeBanner) {

        if (demoMode) {

            demoModeBanner.classList.remove(
                "hidden"
            );
        }
        else {

            demoModeBanner.classList.add(
                "hidden"
            );
        }
    }


    if (dataSourceLabel) {

        dataSourceLabel.textContent =
            demoMode
                ? "Safe demo data"
                : "Live backend data";
    }


    if (backendDataBanner) {

        backendDataBanner.textContent =
            demoMode
                ? "Viewing safe demo data"
                : "Viewing live backend data";
    }
}


/* ============================================================
   Favorites
============================================================ */


function loadFavorites() {

    try {

        const stored =
            localStorage.getItem(
                "nzOpportunityFavorites"
            );

        if (!stored) {

            return new Set();
        }

        const parsed =
            JSON.parse(stored);

        return new Set(
            Array.isArray(parsed)
                ? parsed
                : []
        );
    }
    catch {

        return new Set();
    }
}


function saveFavorites() {

    localStorage.setItem(
        "nzOpportunityFavorites",
        JSON.stringify(
            [...favoriteIds]
        )
    );
}


function opportunityId(item) {

    return (
        `${item.title || ""}::` +
        `${item.source_link || ""}`
    );
}


function toggleFavorite(item) {

    const id =
        opportunityId(item);

    if (
        favoriteIds.has(id)
    ) {

        favoriteIds.delete(id);
    }
    else {

        favoriteIds.add(id);
    }

    saveFavorites();

    renderOpportunities();
}


/* ============================================================
   System health
============================================================ */


async function loadSystemHealth() {

    const [
        health,
        weekly,
        successful
    ] = await Promise.all([
        fetchJson(PATHS.health),
        fetchJson(PATHS.weekly),
        fetchJson(PATHS.successful)
    ]);


    renderDemoMode(
        weekly
    );


    renderSystemHealth(
        health,
        weekly,
        successful
    );
}


function renderSystemHealth(
    health,
    weekly,
    successful
) {

    const banner =
        document.getElementById(
            "system-health-banner"
        );


    const status =
        String(
            health?.status ||
            "unknown"
        ).toLowerCase();


    if (banner) {

        banner.textContent =
            `System Health: ${status.toUpperCase()}`;

        banner.className =
            "health-banner";


        if (status === "healthy") {

            banner.classList.add(
                "health-healthy"
            );
        }
        else if (
            status === "warning"
        ) {

            banner.classList.add(
                "health-warning"
            );
        }
        else {

            banner.classList.add(
                "health-unhealthy"
            );
        }
    }


    text(
        "health-last-run",
        formatDateTime(
            weekly?.finished_at
        )
    );


    text(
        "health-last-success",
        formatDateTime(
            successful?.finished_at
        )
    );


    text(
        "health-duration",
        formatDuration(
            weekly?.duration_seconds
        )
    );


    text(
        "health-production",
        health?.summary
            ?.production_entries,
        "0"
    );


    text(
        "health-run-status",
        weekly?.status
    );


    const stageLabel =
        document.getElementById(
            "run-stage-label"
        );


    if (stageLabel) {

        if (
            weekly?.status === "failed"
        ) {

            stageLabel.textContent =
                "Failure Stage";
        }
        else {

            stageLabel.textContent =
                "Run Stage";
        }
    }


    text(
        "health-failure-stage",
        weekly?.failure_stage
    );


    text(
        "health-rollback",
        weekly?.rollback_performed
            ? "Yes"
            : "No"
    );


    const validation =
        weekly?.validation || {};


    text(
        "health-approved",
        validation.approved,
        "0"
    );


    text(
        "health-review",
        validation.needs_review,
        "0"
    );


    text(
        "health-rejected",
        validation.rejected,
        "0"
    );


    const lifecycle =
        weekly?.lifecycle || {};


    text(
        "health-active",
        lifecycle.active,
        "0"
    );


    text(
        "health-uncertain",
        lifecycle.uncertain,
        "0"
    );


    text(
        "health-expired",
        lifecycle.expired,
        "0"
    );


    text(
        "health-transaction-backup",
        weekly?.transaction_backup_file
            ? fileNameFromPath(
                weekly.transaction_backup_file
            )
            : "none"
    );


    text(
        "page-last-updated",
        formatDateTime(
            weekly?.finished_at
        )
    );


    renderHealthIssues(
        health?.issues || []
    );


    renderComponentHealth(
        health?.checks || []
    );
}


function renderHealthIssues(issues) {

    const container =
        document.getElementById(
            "health-issues"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (
        !Array.isArray(issues) ||
        issues.length === 0
    ) {

        container.textContent =
            "No health issues detected.";

        container.className =
            "health-issues-none";

        return;
    }


    container.className = "";


    const list =
        document.createElement(
            "ul"
        );


    for (
        const issue
        of issues
    ) {

        const item =
            document.createElement(
                "li"
            );

        item.textContent =
            issue;

        list.appendChild(
            item
        );
    }


    container.appendChild(
        list
    );
}


function renderComponentHealth(checks) {

    const container =
        document.getElementById(
            "component-health-list"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (
        !Array.isArray(checks) ||
        checks.length === 0
    ) {

        container.textContent =
            "No component health data available.";

        return;
    }


    const labels = {

        weekly_automation:
            "Weekly Automation",

        validation:
            "Validation",

        lifecycle:
            "Lifecycle",

        refresh:
            "Refresh",

        production_batch:
            "Production Batch"
    };


    for (
        const check
        of checks
    ) {

        const row =
            document.createElement(
                "div"
            );

        row.className =
            "component-health-row";


        const name =
            document.createElement(
                "span"
            );

        name.className =
            "component-health-name";

        name.textContent =
            labels[check.name] ||
            check.name ||
            "Unknown";


        const status =
            document.createElement(
                "span"
            );

        status.className =
            "component-health-status";


        if (check.ok) {

            status.textContent =
                "HEALTHY";

            status.classList.add(
                "component-ok"
            );
        }
        else {

            status.textContent =
                "UNHEALTHY";

            status.classList.add(
                "component-bad"
            );
        }


        row.appendChild(
            name
        );

        row.appendChild(
            status
        );

        container.appendChild(
            row
        );
    }
}


/* ============================================================
   Refresh
============================================================ */


async function loadRefreshStatus() {

    try {

        const refresh =
            await fetchJson(
                PATHS.refresh
            );


        text(
            "refresh-status",
            refresh.status
        );


        text(
            "refresh-started",
            formatDateTime(
                refresh.started_at
            )
        );


        text(
            "refresh-finished",
            formatDateTime(
                refresh.finished_at
            )
        );


        text(
            "refresh-message",
            refresh.message
        );


        text(
            "refresh-history-json",
            fileNameFromPath(
                refresh.latest_history_json
            )
        );


        text(
            "refresh-changes-json",
            fileNameFromPath(
                refresh.latest_changes_json
            )
        );
    }
    catch (
        error
    ) {

        console.error(
            "Unable to load refresh status:",
            error
        );


        text(
            "refresh-status",
            "unavailable"
        );
    }
}


/* ============================================================
   Batch
============================================================ */


async function loadBatchStatus() {

    try {

        const batch =
            await fetchJson(
                PATHS.batch
            );


        text(
            "batch-exists",
            batch.exists
                ? "yes"
                : "no"
        );


        const count =
            Number(
                batch.entry_count || 0
            );


        text(
            "batch-entries",
            count
        );


        text(
            "batch-updated",
            formatDateTime(
                batch.updated_at
            )
        );


        text(
            "batch-generated",
            formatDateTime(
                batch.generated_at
            )
        );


        text(
            "batch-file",
            batch.batch_file
        );


        const badge =
            document.getElementById(
                "batch-workflow-state"
            );


        if (badge) {

            badge.textContent =
                count > 0
                    ? "Batch workflow state: Production Ready"
                    : "Batch workflow state: Empty";
        }


        renderBatchTitles(
            batch.titles || []
        );
    }
    catch (
        error
    ) {

        console.error(
            "Unable to load batch status:",
            error
        );


        text(
            "batch-entries",
            "unavailable"
        );
    }
}


function renderBatchTitles(titles) {

    const container =
        document.getElementById(
            "batch-title-list"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (
        !Array.isArray(titles) ||
        titles.length === 0
    ) {

        container.textContent =
            "No title list available.";

        return;
    }


    container.className =
        "batch-title-list";


    for (
        const title
        of titles
    ) {

        const chip =
            document.createElement(
                "span"
            );

        chip.className =
            "batch-title-chip";

        chip.textContent =
            title;

        container.appendChild(
            chip
        );
    }
}


/* ============================================================
   Opportunities
============================================================ */


async function loadOpportunities() {

    const status =
        document.getElementById(
            "opportunities-status"
        );


    try {

        const data =
            await fetchJson(
                PATHS.opportunities
            );


        if (
            Array.isArray(data)
        ) {

            allOpportunities =
                data;
        }
        else if (
            Array.isArray(
                data?.opportunities
            )
        ) {

            allOpportunities =
                data.opportunities;
        }
        else {

            allOpportunities = [];
        }


        populateTypeFilter();

        renderOpportunities();


        if (status) {

            status.textContent =
                `${allOpportunities.length} production opportunities loaded.`;
        }
    }
    catch (
        error
    ) {

        console.error(
            "Unable to load opportunities:",
            error
        );


        allOpportunities = [];


        if (status) {

            status.textContent =
                "Unable to load live opportunity data.";
        }


        renderOpportunities();
    }
}


function populateTypeFilter() {

    const select =
        document.getElementById(
            "type-filter"
        );


    if (!select) {
        return;
    }


    const types =
        [
            ...new Set(
                allOpportunities
                    .map(
                        item =>
                            item.type
                    )
                    .filter(
                        Boolean
                    )
            )
        ].sort();


    select.innerHTML =
        '<option value="">All Types</option>';


    for (
        const type
        of types
    ) {

        const option =
            document.createElement(
                "option"
            );

        option.value =
            type;

        option.textContent =
            type;

        select.appendChild(
            option
        );
    }
}


function getFilteredOpportunities() {

    const searchInput =
        document.getElementById(
            "search-input"
        );


    const typeFilter =
        document.getElementById(
            "type-filter"
        );


    const scoreFilter =
        document.getElementById(
            "score-filter"
        );


    const favoritesFilter =
        document.getElementById(
            "favorites-filter"
        );


    const search =
        (
            searchInput?.value ||
            ""
        ).toLowerCase();


    const type =
        typeFilter?.value ||
        "";


    const minimumScore =
        Number(
            scoreFilter?.value ||
            0
        );


    const favoritesOnly =
        favoritesFilter?.checked ||
        false;


    return allOpportunities.filter(
        opportunity => {

            const searchable =
                [
                    opportunity.title,
                    opportunity.type,
                    opportunity.where,
                    opportunity.why_fit,
                    opportunity.next_step
                ]
                    .filter(
                        Boolean
                    )
                    .join(" ")
                    .toLowerCase();


            return (
                (
                    !search ||
                    searchable.includes(
                        search
                    )
                ) &&
                (
                    !type ||
                    opportunity.type === type
                ) &&
                (
                    Number(
                        opportunity.total_score ||
                        0
                    ) >= minimumScore
                ) &&
                (
                    !favoritesOnly ||
                    favoriteIds.has(
                        opportunityId(
                            opportunity
                        )
                    )
                )
            );
        }
    );
}


function renderOpportunities() {

    const container =
        document.getElementById(
            "opportunity-list"
        );


    if (!container) {
        return;
    }


    const opportunities =
        getFilteredOpportunities();


    text(
        "visible-count",
        opportunities.length,
        "0"
    );


    container.innerHTML = "";


    if (
        opportunities.length === 0
    ) {

        container.innerHTML =
            `
            <div class="empty-state">
                No opportunities match the current filters.
            </div>
            `;

        return;
    }


    for (
        const opportunity
        of opportunities
    ) {

        container.appendChild(
            createOpportunityCard(
                opportunity
            )
        );
    }
}


function createOpportunityCard(
    opportunity
) {

    const card =
        document.createElement(
            "article"
        );


    card.className =
        "opportunity-card";


    const favorite =
        favoriteIds.has(
            opportunityId(
                opportunity
            )
        );


    card.innerHTML = `
        <div class="opportunity-card-header">

            <div>

                <h3 class="opportunity-title">
                    ${escapeHtml(
                        opportunity.title
                    )}
                </h3>

                <div class="opportunity-type">
                    ${escapeHtml(
                        opportunity.type
                    )}
                </div>

            </div>


            <button
                class="favorite-button ${
                    favorite
                        ? "active"
                        : ""
                }"
                type="button"
                aria-label="Toggle favorite"
            >
                ${
                    favorite
                        ? "★"
                        : "☆"
                }
            </button>

        </div>


        <div class="opportunity-meta">

            <div>
                <strong>Where:</strong>

                ${escapeHtml(
                    opportunity.where
                )}
            </div>


            <div>
                <strong>Date / Deadline:</strong>

                ${escapeHtml(
                    opportunity.date_deadline
                )}
            </div>

        </div>


        <div class="opportunity-description">

            <p>
                <strong>Why it fits:</strong>

                ${escapeHtml(
                    opportunity.why_fit
                )}
            </p>


            <p>
                <strong>Next step:</strong>

                ${escapeHtml(
                    opportunity.next_step
                )}
            </p>

        </div>


        <div class="score-row">

            ${scoreChip(
                "Relevance",
                opportunity.relevance
            )}

            ${scoreChip(
                "Beginner Fit",
                opportunity.beginner_fit
            )}

            ${scoreChip(
                "Career Value",
                opportunity.career_value
            )}

            ${scoreChip(
                "Practicality",
                opportunity.practicality
            )}

            ${scoreChip(
                "University Fit",
                opportunity.university_fit
            )}

            <span class="score-chip total-score">
                Total ${
                    escapeHtml(
                        opportunity.total_score
                    )
                }/25
            </span>

        </div>


        ${
            opportunity.source_link
                ? `
                <div class="source-row">

                    <a
                        class="source-link"
                        href="${
                            escapeHtml(
                                opportunity.source_link
                            )
                        }"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Open Source
                    </a>

                </div>
                `
                : ""
        }
    `;


    const favoriteButton =
        card.querySelector(
            ".favorite-button"
        );


    if (favoriteButton) {

        favoriteButton.addEventListener(
            "click",
            () => {

                toggleFavorite(
                    opportunity
                );
            }
        );
    }


    return card;
}


function scoreChip(
    label,
    value
) {

    if (
        value === undefined ||
        value === null
    ) {

        return "";
    }


    return `
        <span class="score-chip">
            ${escapeHtml(label)}
            ${escapeHtml(value)}/5
        </span>
    `;
}


/* ============================================================
   Events
============================================================ */


function attachEventListeners() {

    const searchInput =
        document.getElementById(
            "search-input"
        );


    const typeFilter =
        document.getElementById(
            "type-filter"
        );


    const scoreFilter =
        document.getElementById(
            "score-filter"
        );


    const favoritesFilter =
        document.getElementById(
            "favorites-filter"
        );


    const refreshHealthButton =
        document.getElementById(
            "refresh-health-button"
        );


    if (searchInput) {

        searchInput.addEventListener(
            "input",
            renderOpportunities
        );
    }


    if (typeFilter) {

        typeFilter.addEventListener(
            "change",
            renderOpportunities
        );
    }


    if (scoreFilter) {

        scoreFilter.addEventListener(
            "change",
            renderOpportunities
        );
    }


    if (favoritesFilter) {

        favoritesFilter.addEventListener(
            "change",
            renderOpportunities
        );
    }


    if (refreshHealthButton) {

        refreshHealthButton.addEventListener(
            "click",
            async event => {

                const button =
                    event.currentTarget;


                button.disabled =
                    true;


                button.textContent =
                    "Refreshing...";


                try {

                    await Promise.all([
                        loadSystemHealth(),
                        loadRefreshStatus(),
                        loadBatchStatus()
                    ]);
                }
                finally {

                    button.disabled =
                        false;


                    button.textContent =
                        "Refresh Health";
                }
            }
        );
    }
}


/* ============================================================
   Startup
============================================================ */


async function initializeDashboard() {

    attachEventListeners();


    try {

        await Promise.all([
            loadSystemHealth(),
            loadRefreshStatus(),
            loadBatchStatus(),
            loadOpportunities()
        ]);
    }
    catch (
        error
    ) {

        console.error(
            "Dashboard initialization failed:",
            error
        );
    }
}


document.addEventListener(
    "DOMContentLoaded",
    initializeDashboard
);