const orderForm = document.querySelector("#order-form");

orderForm.addEventListener("submit", function(event) {
    event.preventDefault();
    console.log("Форма перехвачена!");

    const orderData = {
        name: document.querySelector("#order-name").value.trim(),
        phone: document.querySelector("#order-phone").value.trim(),
        email: document.querySelector("#order-email").value.trim(),
        address: document.querySelector("#order-address").value.trim()
    };

    const cartItems = JSON.parse(localStorage.getItem("cart")) || [];

    orderData.cart = cartItems.map(product => ({
        id: product.id,
        quantity: product.quantity
    }));

    console.log("Полные данные заказа:", orderData);
    console.log("Товары для отправки:", orderData.cart);

    fetch("/order", {
        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify(orderData)
    })
.then(async response => {
    const result = await response.json();

    console.log("Ответ сервера:", result);

    if (!response.ok || !result.success) {
        throw new Error(result.message || "Не удалось оформить заказ");
    }

    // Очищение корзины
    cart = [];

    localStorage.removeItem("cart");

    // Обновление отображение корзины
    renderCart();

    // Показ подтверждения
    const orderMessage = document.querySelector("#order-message");

    orderMessage.textContent =
        `Заказ №${result.order_id} успешно оформлен! Сумма: ${result.total_price.toLocaleString("ru-RU")} ₸`;

    // Очищение формы
    orderForm.reset();
})
.catch(error => {
    console.error("Ошибка отправки заказа:", error);

    const orderMessage = document.querySelector("#order-message");

    orderMessage.textContent = error.message;
});


    console.log("Данные покупателя:", orderData);
});


