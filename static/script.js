let expenses = [];
let incomes = [];

let editingExpenseId = null;

let categoryBarChart = null;
let categoryPieChart = null;
let monthlyChart = null;

// =========================================================
// ELEMENTS
// =========================================================

// Expense elements

const form =
    document.getElementById("expenseForm");

const amountInput =
    document.getElementById("amount");

const categoryInput =
    document.getElementById("category");

const descriptionInput =
    document.getElementById("description");

const dateInput =
    document.getElementById("expenseDate");

const expenseTable =
    document.getElementById("expenseTable");

const searchInput =
    document.getElementById("searchInput");

const submitButton =
    document.getElementById("submitButton");

const formTitle =
    document.getElementById("formTitle");

const totalAmount =
    document.getElementById("totalAmount");

const totalRecords =
    document.getElementById("totalRecords");

const highestCategory =
    document.getElementById("highestCategory");

const categorySummary =
    document.getElementById("categorySummary");

const monthFilter =
    document.getElementById("monthFilter");

// Income elements

const incomeForm =
    document.getElementById("incomeForm");

const incomeAmount =
    document.getElementById("incomeAmount");

const incomeSource =
    document.getElementById("incomeSource");

const incomeDescription =
    document.getElementById("incomeDescription");

const incomeDate =
    document.getElementById("incomeDate");

const incomeTable =
    document.getElementById("incomeTable");

const totalIncome =
    document.getElementById("totalIncome");

const balanceAmount =
    document.getElementById("balanceAmount");

// Budget elements

const monthlyBudget =
    document.getElementById("monthlyBudget");

const remainingBudget =
    document.getElementById("remainingBudget");

const budgetForm =
    document.getElementById("budgetForm");

const budgetMonth =
    document.getElementById("budgetMonth");

const budgetAmount =
    document.getElementById("budgetAmount");

const budgetWarning =
    document.getElementById("budgetWarning");

const budgetProgress =
    document.getElementById("budgetProgress");

const budgetPercentage =
    document.getElementById("budgetPercentage");

// Statistics

const averageExpense =
    document.getElementById("averageExpense");

const largestExpense =
    document.getElementById("largestExpense");

const topCategory =
    document.getElementById("topCategory");


// =========================================================
// PAGE LOAD
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    async function () {

        setTodayDate();

        setIncomeDate();

        setCurrentMonth();

        await loadExpenses();

        await loadIncome();

        await loadCategorySummary();

        await loadMonthlySummary();

        await loadBudget();

        await loadStatistics();

    }
);


// =========================================================
// SET TODAY'S EXPENSE DATE
// =========================================================

function setTodayDate() {

    if (!dateInput) {
        return;
    }

    const today =
        new Date()
            .toISOString()
            .split("T")[0];

    dateInput.value = today;
}


// =========================================================
// SET TODAY'S INCOME DATE
// =========================================================

function setIncomeDate() {

    if (!incomeDate) {
        return;
    }

    const today =
        new Date()
            .toISOString()
            .split("T")[0];

    incomeDate.value = today;
}


// =========================================================
// SET CURRENT MONTH
// =========================================================

function setCurrentMonth() {

    if (!budgetMonth) {
        return;
    }

    const today =
        new Date();

    const year =
        today.getFullYear();

    const month =
        String(
            today.getMonth() + 1
        ).padStart(2, "0");

    budgetMonth.value =
        `${year}-${month}`;
}


// =========================================================
// LOAD EXPENSES
// =========================================================

async function loadExpenses() {

    try {

        const response =
            await fetch("/api/expenses");

        const data =
            await response.json();

        if (!response.ok) {

            console.error(
                "Expense error:",
                data.error
            );

            return;
        }

        expenses = data;

        displayExpenses(expenses);

        updateSummary();

    }

    catch (error) {

        console.error(
            "LOAD EXPENSE ERROR:",
            error
        );

    }
}


// =========================================================
// DISPLAY EXPENSES
// =========================================================

function displayExpenses(expenseList) {

    if (!expenseTable) {
        return;
    }

    expenseTable.innerHTML = "";

    if (expenseList.length === 0) {

        expenseTable.innerHTML = `

            <tr>

                <td
                    colspan="6"
                    class="no-data"
                >
                    No expenses found.
                </td>

            </tr>

        `;

        return;
    }

    expenseList.forEach(
        function (expense) {

            const row =
                document.createElement("tr");

            row.innerHTML = `

                <td>
                    ${expense.id}
                </td>

                <td>
                    ₹${Number(
                        expense.amount
                    ).toFixed(2)}
                </td>

                <td>
                    ${escapeHTML(
                        expense.category
                    )}
                </td>

                <td>
                    ${escapeHTML(
                        expense.description || ""
                    )}
                </td>

                <td>
                    ${expense.expense_date}
                </td>

                <td>

                    <button
                        class="edit-button"
                        onclick="editExpense(${expense.id})"
                    >
                        Edit
                    </button>

                    <button
                        class="delete-button"
                        onclick="deleteExpense(${expense.id})"
                    >
                        Delete
                    </button>

                </td>

            `;

            expenseTable.appendChild(row);

        }
    );
}


// =========================================================
// ADD / UPDATE EXPENSE
// =========================================================

if (form) {

    form.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            const amount =
                amountInput.value;

            const category =
                categoryInput.value;

            const description =
                descriptionInput.value.trim();

            const expenseDate =
                dateInput.value;

            if (
                !amount ||
                !category ||
                !expenseDate
            ) {

                alert(
                    "Please fill all required fields."
                );

                return;
            }

            if (Number(amount) <= 0) {

                alert(
                    "Amount must be greater than zero."
                );

                return;
            }

            const expenseData = {

                amount: amount,

                category: category,

                description: description,

                expense_date: expenseDate

            };

            try {

                let response;

                if (
                    editingExpenseId !== null
                ) {

                    response =
                        await fetch(
                            `/api/expenses/${editingExpenseId}`,
                            {

                                method: "PUT",

                                headers: {
                                    "Content-Type":
                                        "application/json"
                                },

                                body:
                                    JSON.stringify(
                                        expenseData
                                    )

                            }
                        );

                }

                else {

                    response =
                        await fetch(
                            "/api/expenses",
                            {

                                method: "POST",

                                headers: {
                                    "Content-Type":
                                        "application/json"
                                },

                                body:
                                    JSON.stringify(
                                        expenseData
                                    )

                            }
                        );

                }

                const result =
                    await response.json();

                if (!response.ok) {

                    alert(
                        result.error ||
                        "Operation failed"
                    );

                    return;
                }

                alert(
                    result.message
                );

                cancelEdit();

                await refreshDashboard();

            }

            catch (error) {

                console.error(
                    "EXPENSE ERROR:",
                    error
                );

                alert(
                    "Unable to connect to the server."
                );

            }

        }
    );
}


// =========================================================
// EDIT EXPENSE
// =========================================================

function editExpense(id) {

    const expense =
        expenses.find(
            function (item) {

                return item.id === id;

            }
        );

    if (!expense) {
        return;
    }

    editingExpenseId = id;

    amountInput.value =
        expense.amount;

    categoryInput.value =
        expense.category;

    descriptionInput.value =
        expense.description || "";

    dateInput.value =
        expense.expense_date;

    formTitle.textContent =
        "Update Expense";

    submitButton.textContent =
        "Update Expense";

    window.scrollTo({

        top: 0,

        behavior: "smooth"

    });
}


// =========================================================
// CANCEL EDIT
// =========================================================

function cancelEdit() {

    editingExpenseId = null;

    if (form) {

        form.reset();

    }

    setTodayDate();

    if (formTitle) {

        formTitle.textContent =
            "Add Expense";

    }

    if (submitButton) {

        submitButton.textContent =
            "Add Expense";

    }
}


// =========================================================
// DELETE EXPENSE
// =========================================================

async function deleteExpense(id) {

    const confirmed =
        confirm(
            "Are you sure you want to delete this expense?"
        );

    if (!confirmed) {
        return;
    }

    try {

        const response =
            await fetch(
                `/api/expenses/${id}`,
                {
                    method: "DELETE"
                }
            );

        const result =
            await response.json();

        if (!response.ok) {

            alert(
                result.error ||
                "Delete failed"
            );

            return;
        }

        alert(
            result.message
        );

        await refreshDashboard();

    }

    catch (error) {

        console.error(
            "DELETE EXPENSE ERROR:",
            error
        );

        alert(
            "Unable to connect to the server."
        );

    }
}


// =========================================================
// SEARCH EXPENSES
// =========================================================

if (searchInput) {

    searchInput.addEventListener(
        "input",
        function () {

            const searchText =
                searchInput.value
                    .toLowerCase()
                    .trim();

            const filteredExpenses =
                expenses.filter(
                    function (expense) {

                        return (

                            String(
                                expense.category
                            )
                                .toLowerCase()
                                .includes(
                                    searchText
                                )

                            ||

                            String(
                                expense.description || ""
                            )
                                .toLowerCase()
                                .includes(
                                    searchText
                                )

                        );

                    }
                );

            displayExpenses(
                filteredExpenses
            );

        }
    );
}


// =========================================================
// UPDATE EXPENSE SUMMARY
// =========================================================

function updateSummary() {

    let total = 0;

    expenses.forEach(
        function (expense) {

            total +=
                Number(expense.amount);

        }
    );

    if (totalAmount) {

        totalAmount.textContent =
            `₹${total.toFixed(2)}`;

    }

    if (totalRecords) {

        totalRecords.textContent =
            expenses.length;

    }

    updateBalance();

}


// =========================================================
// LOAD INCOME
// =========================================================

async function loadIncome() {

    try {

        const response =
            await fetch("/api/income");

        const data =
            await response.json();

        if (!response.ok) {

            console.error(
                "INCOME ERROR:",
                data.error
            );

            return;
        }

        incomes = data;

        displayIncome(incomes);

        updateTotalIncome(incomes);

    }

    catch (error) {

        console.error(
            "LOAD INCOME ERROR:",
            error
        );

    }
}


// =========================================================
// DISPLAY INCOME
// =========================================================

function displayIncome(incomeList) {

    if (!incomeTable) {
        return;
    }

    incomeTable.innerHTML = "";

    if (incomeList.length === 0) {

        incomeTable.innerHTML = `

            <tr>

                <td
                    colspan="6"
                    class="no-data"
                >
                    No income records found.
                </td>

            </tr>

        `;

        return;
    }

    incomeList.forEach(
        function (income) {

            const row =
                document.createElement("tr");

            row.innerHTML = `

                <td>
                    ${income.id}
                </td>

                <td>
                    ₹${Number(
                        income.amount
                    ).toFixed(2)}
                </td>

                <td>
                    ${escapeHTML(
                        income.source
                    )}
                </td>

                <td>
                    ${escapeHTML(
                        income.description || ""
                    )}
                </td>

                <td>
                    ${income.income_date}
                </td>

                <td>

                    <button
                        class="delete-button"
                        onclick="deleteIncome(${income.id})"
                    >
                        Delete
                    </button>

                </td>

            `;

            incomeTable.appendChild(row);

        }
    );
}


// =========================================================
// UPDATE TOTAL INCOME
// =========================================================

function updateTotalIncome(incomeList) {

    let total = 0;

    incomeList.forEach(
        function (income) {

            total +=
                Number(income.amount);

        }
    );

    if (totalIncome) {

        totalIncome.textContent =
            `₹${total.toFixed(2)}`;

    }

    updateBalance();
}


// =========================================================
// UPDATE BALANCE
// =========================================================

function updateBalance() {

    let incomeTotal = 0;

    let expenseTotal = 0;

    incomes.forEach(
        function (income) {

            incomeTotal +=
                Number(income.amount);

        }
    );

    expenses.forEach(
        function (expense) {

            expenseTotal +=
                Number(expense.amount);

        }
    );

    const balance =
        incomeTotal - expenseTotal;

    if (balanceAmount) {

        balanceAmount.textContent =
            `₹${balance.toFixed(2)}`;

    }
}


// =========================================================
// ADD INCOME
// =========================================================

if (incomeForm) {

    incomeForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            const amount =
                incomeAmount.value;

            const source =
                incomeSource.value.trim();

            const description =
                incomeDescription.value.trim();

            const income_date =
                incomeDate.value;

            if (
                !amount ||
                !source ||
                !income_date
            ) {

                alert(
                    "Please fill all required income fields."
                );

                return;
            }

            if (Number(amount) <= 0) {

                alert(
                    "Income amount must be greater than zero."
                );

                return;
            }

            try {

                const response =
                    await fetch(
                        "/api/income",
                        {

                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify({

                                    amount:
                                        amount,

                                    source:
                                        source,

                                    description:
                                        description,

                                    income_date:
                                        income_date

                                })

                        }
                    );

                const result =
                    await response.json();

                if (!response.ok) {

                    alert(
                        result.error ||
                        "Failed to add income"
                    );

                    return;
                }

                alert(
                    result.message
                );

                incomeForm.reset();

                setIncomeDate();

                await loadIncome();

            }

            catch (error) {

                console.error(
                    "ADD INCOME ERROR:",
                    error
                );

                alert(
                    "Unable to connect to the server."
                );

            }

        }
    );
}


// =========================================================
// DELETE INCOME
// =========================================================

async function deleteIncome(id) {

    const confirmed =
        confirm(
            "Are you sure you want to delete this income?"
        );

    if (!confirmed) {
        return;
    }

    try {

        const response =
            await fetch(
                `/api/income/${id}`,
                {
                    method: "DELETE"
                }
            );

        const result =
            await response.json();

        if (!response.ok) {

            alert(
                result.error ||
                "Failed to delete income"
            );

            return;
        }

        alert(
            result.message
        );

        await loadIncome();

    }

    catch (error) {

        console.error(
            "DELETE INCOME ERROR:",
            error
        );

        alert(
            "Unable to connect to the server."
        );

    }
}


// =========================================================
// CATEGORY SUMMARY
// =========================================================

async function loadCategorySummary() {

    try {

        const response =
            await fetch("/api/summary");

        const data =
            await response.json();

        if (!response.ok) {

            console.error(
                data.error
            );

            return;
        }

        if (!categorySummary) {
            return;
        }

        categorySummary.innerHTML = "";

        if (data.length === 0) {

            categorySummary.innerHTML = `

                <p>
                    No category data available.
                </p>

            `;

            if (highestCategory) {

                highestCategory.textContent =
                    "-";

            }

            updateCategoryCharts([]);

            return;
        }

        data.forEach(
            function (item) {

                const card =
                    document.createElement("div");

                card.className =
                    "category-card";

                card.innerHTML = `

                    <h3>
                        ${escapeHTML(
                            item.category
                        )}
                    </h3>

                    <p>
                        ₹${Number(
                            item.total
                        ).toFixed(2)}
                    </p>

                `;

                categorySummary.appendChild(
                    card
                );

            }
        );

        if (highestCategory) {

            highestCategory.textContent =
                data[0].category;

        }

        updateCategoryCharts(data);

    }

    catch (error) {

        console.error(
            "CATEGORY SUMMARY ERROR:",
            error
        );

    }
}


// =========================================================
// CATEGORY CHARTS
// =========================================================

function updateCategoryCharts(data) {

    const barCanvas =
        document.getElementById(
            "categoryBarChart"
        );

    const pieCanvas =
        document.getElementById(
            "categoryPieChart"
        );

    if (!barCanvas || !pieCanvas) {
        return;
    }

    const labels =
        data.map(
            function (item) {

                return item.category;

            }
        );

    const values =
        data.map(
            function (item) {

                return Number(item.total);

            }
        );

    if (categoryBarChart) {

        categoryBarChart.destroy();

    }

    if (categoryPieChart) {

        categoryPieChart.destroy();

    }

    const barContext =
        barCanvas.getContext("2d");

    categoryBarChart =
        new Chart(
            barContext,
            {

                type: "bar",

                data: {

                    labels: labels,

                    datasets: [

                        {

                            label:
                                "Amount Spent",

                            data: values

                        }

                    ]

                },

                options: {

                    responsive: true,

                    scales: {

                        y: {

                            beginAtZero: true

                        }

                    }

                }

            }
        );

    const pieContext =
        pieCanvas.getContext("2d");

    categoryPieChart =
        new Chart(
            pieContext,
            {

                type: "doughnut",

                data: {

                    labels: labels,

                    datasets: [

                        {

                            data: values

                        }

                    ]

                },

                options: {

                    responsive: true

                }

            }
        );
}


// =========================================================
// MONTHLY SUMMARY
// =========================================================

async function loadMonthlySummary() {

    try {

        const response =
            await fetch(
                "/api/monthly-summary"
            );

        const data =
            await response.json();

        if (!response.ok) {

            console.error(
                data.error
            );

            return;
        }

        populateMonthFilter(data);

        updateMonthlyChart(data);

    }

    catch (error) {

        console.error(
            "MONTHLY SUMMARY ERROR:",
            error
        );

    }
}


// =========================================================
// MONTH FILTER
// =========================================================

function populateMonthFilter(data) {

    if (!monthFilter) {
        return;
    }

    const currentValue =
        monthFilter.value;

    monthFilter.innerHTML = `

        <option value="all">
            All Months
        </option>

    `;

    data.forEach(
        function (item) {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                item.month;

            option.textContent =
                item.month;

            monthFilter.appendChild(
                option
            );

        }
    );

    const exists =
        [...monthFilter.options]
            .some(
                function (option) {

                    return (
                        option.value ===
                        currentValue
                    );

                }
            );

    if (exists) {

        monthFilter.value =
            currentValue;

    }
}


if (monthFilter) {

    monthFilter.addEventListener(
        "change",
        async function () {

            await loadMonthlySummary();

        }
    );
}


// =========================================================
// MONTHLY CHART
// =========================================================

function updateMonthlyChart(data) {

    const canvas =
        document.getElementById(
            "monthlyChart"
        );

    if (!canvas) {
        return;
    }

    const selectedMonth =
        monthFilter
            ? monthFilter.value
            : "all";

    let filteredData =
        data;

    if (
        selectedMonth !== "all"
    ) {

        filteredData =
            data.filter(
                function (item) {

                    return (
                        item.month ===
                        selectedMonth
                    );

                }
            );

    }

    const labels =
        filteredData.map(
            function (item) {

                return item.month;

            }
        );

    const values =
        filteredData.map(
            function (item) {

                return Number(
                    item.total
                );

            }
        );

    if (monthlyChart) {

        monthlyChart.destroy();

    }

    const context =
        canvas.getContext("2d");

    monthlyChart =
        new Chart(
            context,
            {

                type: "line",

                data: {

                    labels: labels,

                    datasets: [

                        {

                            label:
                                "Monthly Expenses",

                            data: values,

                            tension: 0.3

                        }

                    ]

                },

                options: {

                    responsive: true,

                    scales: {

                        y: {

                            beginAtZero: true

                        }

                    }

                }

            }
        );
}


// =========================================================
// LOAD BUDGET
// =========================================================

async function loadBudget() {

    if (!budgetMonth) {
        return;
    }

    const month =
        budgetMonth.value;

    if (!month) {
        return;
    }

    try {

        const response =
            await fetch(
                `/api/budget-status?month=${month}`
            );

        const data =
            await response.json();

        if (!response.ok) {

            console.error(
                "BUDGET ERROR:",
                data.error
            );

            return;
        }

        if (monthlyBudget) {

            monthlyBudget.textContent =
                `₹${Number(
                    data.budget
                ).toFixed(2)}`;

        }

        if (remainingBudget) {

            remainingBudget.textContent =
                `₹${Number(
                    data.remaining
                ).toFixed(2)}`;

        }

        updateBudgetProgress(data);

        updateBudgetWarning(data);

    }

    catch (error) {

        console.error(
            "LOAD BUDGET ERROR:",
            error
        );

    }
}


// =========================================================
// BUDGET PROGRESS
// =========================================================

function updateBudgetProgress(data) {

    if (!budgetProgress) {
        return;
    }

    let percentage =
        Number(data.percentage) || 0;

    if (percentage < 0) {
        percentage = 0;
    }

    const displayPercentage =
        Math.min(
            percentage,
            100
        );

    budgetProgress.style.width =
        `${displayPercentage}%`;

    if (budgetPercentage) {

        budgetPercentage.textContent =
            `${percentage.toFixed(1)}%`;

    }

}


// =========================================================
// BUDGET WARNING
// =========================================================

function updateBudgetWarning(data) {

    if (!budgetWarning) {
        return;
    }

    budgetWarning.classList.remove(
        "hidden"
    );

    if (
        !data.budget ||
        Number(data.budget) <= 0
    ) {

        budgetWarning.textContent =
            "No budget has been set for this month.";

        return;
    }

    const percentage =
        Number(data.percentage);

    if (percentage >= 100) {

        budgetWarning.textContent =
            "⚠️ Budget exceeded! You have spent more than your monthly budget.";

    }

    else if (percentage >= 80) {

        budgetWarning.textContent =
            "⚠️ Warning: You have used more than 80% of your monthly budget.";

    }

    else if (percentage >= 60) {

        budgetWarning.textContent =
            "⚠️ You have used more than 60% of your monthly budget.";

    }

    else {

        budgetWarning.textContent =
            "✅ You are within your monthly budget.";

    }
}


// =========================================================
// SAVE BUDGET
// =========================================================

if (budgetForm) {

    budgetForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            const month =
                budgetMonth.value;

            const amount =
                budgetAmount.value;

            if (!month || !amount) {

                alert(
                    "Please enter month and budget amount."
                );

                return;
            }

            if (Number(amount) <= 0) {

                alert(
                    "Budget must be greater than zero."
                );

                return;
            }

            try {

                const response =
                    await fetch(
                        "/api/budget",
                        {

                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify({

                                    month:
                                        month,

                                    amount:
                                        amount

                                })

                        }
                    );

                const result =
                    await response.json();

                if (!response.ok) {

                    alert(
                        result.error ||
                        "Failed to save budget"
                    );

                    return;
                }

                alert(
                    result.message
                );

                budgetAmount.value = "";

                await loadBudget();

            }

            catch (error) {

                console.error(
                    "SAVE BUDGET ERROR:",
                    error
                );

                alert(
                    "Unable to connect to the server."
                );

            }

        }
    );
}


// =========================================================
// CHANGE BUDGET MONTH
// =========================================================

if (budgetMonth) {

    budgetMonth.addEventListener(
        "change",
        async function () {

            await loadBudget();

        }
    );
}


// =========================================================
// STATISTICS
// =========================================================

async function loadStatistics() {

    try {

        const response =
            await fetch(
                "/api/statistics"
            );

        if (!response.ok) {

            console.log(
                "Statistics endpoint not available."
            );

            calculateStatisticsLocally();

            return;
        }

        const data =
            await response.json();

        if (averageExpense) {

            averageExpense.textContent =
                `₹${Number(
                    data.average
                ).toFixed(2)}`;

        }

        if (largestExpense) {

            largestExpense.textContent =
                `₹${Number(
                    data.largest
                ).toFixed(2)}`;

        }

        if (topCategory) {

            topCategory.textContent =
                data.top_category || "-";

        }

    }

    catch (error) {

        console.error(
            "STATISTICS ERROR:",
            error
        );

        calculateStatisticsLocally();

    }
}


// =========================================================
// LOCAL STATISTICS FALLBACK
// =========================================================

function calculateStatisticsLocally() {

    if (expenses.length === 0) {

        if (averageExpense) {
            averageExpense.textContent =
                "₹0.00";
        }

        if (largestExpense) {
            largestExpense.textContent =
                "₹0.00";
        }

        if (topCategory) {
            topCategory.textContent =
                "-";
        }

        return;
    }

    let total = 0;

    let largest = 0;

    const categories = {};

    expenses.forEach(
        function (expense) {

            const amount =
                Number(expense.amount);

            total += amount;

            if (amount > largest) {
                largest = amount;
            }

            if (
                !categories[
                    expense.category
                ]
            ) {

                categories[
                    expense.category
                ] = 0;

            }

            categories[
                expense.category
            ] += amount;

        }
    );

    let highestCategoryName = "-";

    let highestCategoryAmount = 0;

    Object.keys(categories)
        .forEach(
            function (category) {

                if (
                    categories[category] >
                    highestCategoryAmount
                ) {

                    highestCategoryAmount =
                        categories[category];

                    highestCategoryName =
                        category;

                }

            }
        );

    const average =
        total / expenses.length;

    if (averageExpense) {

        averageExpense.textContent =
            `₹${average.toFixed(2)}`;

    }

    if (largestExpense) {

        largestExpense.textContent =
            `₹${largest.toFixed(2)}`;

    }

    if (topCategory) {

        topCategory.textContent =
            highestCategoryName;

    }
}


// =========================================================
// CSV EXPORT
// =========================================================

function exportCSV() {

    if (expenses.length === 0) {

        alert(
            "There are no expenses to export."
        );

        return;
    }

    let csv =
        "ID,Amount,Category,Description,Date\n";

    expenses.forEach(
        function (expense) {

            csv +=
                `"${expense.id}",` +
                `"${expense.amount}",` +
                `"${escapeCSV(expense.category)}",` +
                `"${escapeCSV(expense.description || "")}",` +
                `"${expense.expense_date}"\n`;

        }
    );

    const blob =
        new Blob(
            [csv],
            {
                type:
                    "text/csv;charset=utf-8;"
            }
        );

    const url =
        URL.createObjectURL(blob);

    const link =
        document.createElement("a");

    link.href = url;

    link.download =
        "smart_expense_report.csv";

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);

    URL.revokeObjectURL(url);
}


// =========================================================
// PDF EXPORT
// =========================================================

function exportPDF() {

    window.print();

}


// =========================================================
// REFRESH DASHBOARD
// =========================================================

async function refreshDashboard() {

    await loadExpenses();

    await loadIncome();

    await loadCategorySummary();

    await loadMonthlySummary();

    await loadBudget();

    await loadStatistics();

}


// =========================================================
// ESCAPE HTML
// =========================================================

function escapeHTML(value) {

    return String(value)
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


// =========================================================
// ESCAPE CSV
// =========================================================

function escapeCSV(value) {

    return String(value)
        .replace(
            /"/g,
            '""'
        );

}