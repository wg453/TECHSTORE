
let cart = JSON.parse(localStorage.getItem("cart")) || [];

const cartItemsContainer = document.querySelector("#cart-items");
const cartEmptyMessage = document.querySelector("#cart-empty");
const cartTotal = document.querySelector("#cart-total");
const cartCount = document.querySelector("#cart-count");
const headerCartCounts = document.querySelectorAll("#header-cart-count");

const addToCartButtons = document.querySelectorAll(".add-to-cart");

function renderCart() {

    let totalQuantity = 0;

cart.forEach(product => {
    totalQuantity += product.quantity;
});

headerCartCounts.forEach(counter => {
    counter.textContent = totalQuantity;
});

    if (!cartItemsContainer) {
        return;
    }

    cartItemsContainer.innerHTML = "";
    let total = 0;

    if (cart.length === 0) {
        cartEmptyMessage.style.display = "block";
        cartTotal.textContent = "0 ₸";
        cartCount.textContent = "0 позиций · 0 товаров";
        return;
    }
    cartEmptyMessage.style.display = "none";

    cart.forEach(product => {

        total += product.price * product.quantity;

        const productElement = document.createElement("div");
        productElement.dataset.productId = product.id;

        productElement.classList.add("cart-item");

        productElement.innerHTML = `
            <div class="cart-item-image">
                <img src="${product.image}" alt="${product.name}">
            </div>

            <div class="cart-item-info">
                <div class="cart-item-brand">${product.brand || ''}</div>
                <div class="cart-item-name">${product.name}</div>
                <div class="cart-item-price">${product.price.toLocaleString("ru-RU")} ₸</div>
            </div>

            <div class="cart-item-controls">
                <div class="cart-quantity">
                    <button class="decrease-quantity" type="button">−</button>
                    <span>${product.quantity}</span>
                    <button class="increase-quantity" type="button">+</button>
                </div>

                <button class="remove-product" type="button">Убрать из корзины</button>
            </div>
        `;

        const removeButton = productElement.querySelector(".remove-product");
            const decreaseButton = productElement.querySelector(".decrease-quantity");

            decreaseButton.addEventListener("click", () => {

                if (product.quantity > 1) {
                    product.quantity -= 1;
                } else {
                    cart = cart.filter(item => item.id !== product.id);
                }

                localStorage.setItem("cart", JSON.stringify(cart));

                renderCart();

        });
            const increaseButton = productElement.querySelector(".increase-quantity");


            increaseButton.addEventListener("click", () => {

                product.quantity += 1;

                localStorage.setItem("cart", JSON.stringify(cart));

                renderCart();

        });

        removeButton.addEventListener("click", () => {

            cart = cart.filter(item => item.id !== product.id);

            localStorage.setItem("cart", JSON.stringify(cart));

            renderCart();

        });

        cartItemsContainer.append(productElement);

    });

    cartTotal.textContent = total.toLocaleString("ru-RU") + " ₸";
    cartCount.textContent = `${cart.length} позиций · ${totalQuantity} товаров`;
}

renderCart();

addToCartButtons.forEach(button => {

    button.addEventListener("click", () => {

        const productId = button.dataset.productId;
        const productName = button.dataset.productName;
        const productPrice = Number(button.dataset.productPrice);
        const productImage = button.closest(".product-card").querySelector(".product-image img").getAttribute("src");

        const existingProduct = cart.find(product => product.id === productId);

        if (existingProduct) {
            existingProduct.quantity += 1;
        } else {
            cart.push({
                id: productId,
                name: productName,
                price: productPrice,
                quantity: 1,
                image: productImage,
                brand: button.closest(".product-card").querySelector(".product-brand").textContent
            });
        }

        localStorage.setItem("cart", JSON.stringify(cart));

        console.log(cart);
        console.log("Путь к изображению:", productImage);

        renderCart();

        showCartToast();

    });

});

const cartToast = document.querySelector("#cart-toast");
let toastTimer;

function showCartToast() {
    cartToast.classList.add("show");

    clearTimeout(toastTimer);

    toastTimer = setTimeout(() => {
        cartToast.classList.remove("show");
    }, 2500);
}