const params = new URLSearchParams(window.location.search);

const productId = params.get("id");

console.log("ID товара:", productId);

    async function loadProduct() {

    const response = await fetch(`/api/products/${productId}`);

    const product = await response.json();

    const productContent = document.querySelector("#product-content");

    const specificationsHTML = product.specifications.map(specification => {
        return `
            <div class="specification">
                <span>${specification.name}</span>
                <span>${specification.value}</span>
            </div>
        `;
    }).join("");

     productContent.innerHTML = `
        <div class="product-details">

        <div class="product-image">
            <img src="${product.image}" alt="${product.name}">
        </div>


            <h1>${product.name}</h1>

            <p class="product-price">
                ${product.price.toLocaleString("ru-RU")} ₸
            </p>

            <p class="product-short-description">
                ${product.short_description}
            </p>

            <h2>Описание товара</h2>

            <p class="product-full-description">
                ${product.full_description}
            </p>

            <h2>Характеристики</h2>

            <div class="specifications">
                ${specificationsHTML}
            </div>

        </div>
    `;

}

loadProduct();