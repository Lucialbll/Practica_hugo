
document.addEventListener("DOMContentLoaded", async () => {
    const input = document.getElementById("search-input");
    const results = document.getElementById("search-results");

    const response = await fetch("/search.json");
    const articles = await response.json();

    input.addEventListener("input", () => {
        const query = input.value.toLowerCase().trim();

        results.innerHTML = "";

        if (query === "") {
            return;
        }

       const filtered = articles
    .filter(article =>
        article.title.toLowerCase().includes(query) ||
        article.text.toLowerCase().includes(query) ||
        article.tags.some(tag => tag.toLowerCase().includes(query))
    )
    .sort((a, b) => {
        const score = article => {
            let points = 0;

            if (article.title.toLowerCase().includes(query)) {
                points += 3;
            }

            if (article.tags.some(tag => tag.toLowerCase().includes(query))) {
                points += 2;
            }

            if (article.text.toLowerCase().includes(query)) {
                points += 1;
            }

            return points;
        };

        return score(b) - score(a);
    });
    

        filtered.forEach(article => {
            const item = document.createElement("div");

            const link = document.createElement("a");
            link.href = article.url;
            link.textContent = article.title;

            item.appendChild(link);
            results.appendChild(item);
        });

        if (filtered.length === 0) {
            results.textContent = "No se encontraron artículos.";
        }
    });
});
