document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("searchInput");
  const authorInput = document.getElementById("authorInput");
  const sortSelect = document.getElementById("sortSelect");
  const table = document.getElementById("notesTable");
  const tbody = table.querySelector("tbody");
  const noResultsMessage = document.getElementById("no-results-message");

  function filterAndSortNotes() {
    const searchValue = searchInput.value.trim().toLowerCase();
    const authorValue = authorInput ? authorInput.value.trim().toLowerCase() : "";
    const sortValue = sortSelect.value;

    // Get all rows
    let rows = Array.from(tbody.querySelectorAll("tr"));

    // Filter rows by title and author
    rows.forEach(row => {
      const titleCell = row.querySelector("td:first-child");
      const authorCell = authorInput ? row.querySelector("td:nth-child(2)") : null;

      const titleText = titleCell ? titleCell.textContent.toLowerCase() : "";
      const authorText = authorCell ? authorCell.textContent.toLowerCase() : "";

      const matchesTitle = titleText.includes(searchValue);
      const matchesAuthor = authorInput ? authorText.includes(authorValue) : true;

      if (matchesTitle && matchesAuthor) {
        row.style.display = "";
      } else {
        row.style.display = "none";
      }
    });

    // Sort visible rows
    rows = rows.filter(row => row.style.display !== "none");

    rows.sort((a, b) => {
      let dateCellIndex = authorInput ? 2 : 1;

      if (sortValue === "newest" || sortValue === "oldest") {
        const dateA = new Date(a.cells[dateCellIndex].textContent);
        const dateB = new Date(b.cells[dateCellIndex].textContent);

        if (sortValue === "newest") {
          return dateB - dateA;
        } else {
          return dateA - dateB;
        }
      } else if (sortValue === "az" || sortValue === "za") {
        const titleA = a.cells[0].textContent.toLowerCase();
        const titleB = b.cells[0].textContent.toLowerCase();

        if (titleA < titleB) return sortValue === "az" ? -1 : 1;
        if (titleA > titleB) return sortValue === "az" ? 1 : -1;
        return 0;
      }
      return 0;
    });

    // Reorder rows in tbody
    rows.forEach(row => tbody.appendChild(row));

    // Show/hide no results message
    if (rows.length === 0) {
      noResultsMessage.style.display = "block";
    } else {
      noResultsMessage.style.display = "none";
    }
  }

  // Event listeners for filters and sort
  searchInput.addEventListener("input", filterAndSortNotes);
  if (authorInput) authorInput.addEventListener("input", filterAndSortNotes);
  sortSelect.addEventListener("change", filterAndSortNotes);

  // Initial filter on page load
  filterAndSortNotes();
});
