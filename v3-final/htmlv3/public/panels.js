const openButton = document.querySelector("#open-login");
const overlay = document.querySelector("#login-overlay");
const closeButton = document.querySelector("#close-login");
const loginForm = document.querySelector("#login-form");
const loginMessage = document.querySelector("#login-message");

// ========================================
// ОФОРМЛЕНИЕ СООБЩЕНИЙ
// ========================================

function setMessage(element, text, type = "info") {
    element.textContent = text;

    element.classList.remove("message-error", "message-success");

    if (type === "error") {
        element.classList.add("message-error");
    } else if (type === "success") {
        element.classList.add("message-success");
    }
}

function openLogin() {
    overlay.classList.add("is-open");
}

function closeLogin() {
    overlay.classList.remove("is-open");
}

openButton.addEventListener("click", function (event) {
    event.preventDefault();
    openLogin();
});

closeButton.addEventListener("click", closeLogin);

overlay.addEventListener("click", function (event) {
    if (event.target === overlay) {
        closeLogin();
    }
});

loginForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    setMessage(loginMessage, "Проверяем данные...", "info");

    try {
        const response = await fetch("/login", {
            method: "POST",
            body: new URLSearchParams(new FormData(loginForm))
        });

        const message = await response.text();

        if (response.ok) {
            setMessage(loginMessage, message, "success");

            closeLogin();
            window.location.href = "index.html";
            await checkSession();
        } else {
            setMessage(loginMessage, message, "error");
        }

    } catch (error) {
        setMessage(
            loginMessage,
            "Не удалось связаться с сервером.",
            "error"
        );

        console.error("Ошибка входа:", error);
    }
});



const guestActions = document.querySelector("#guest-actions");
const profileLink = document.querySelector("#profile-link");
    if (profileLink && window.location.pathname.endsWith("/profile.html")) {
        profileLink.classList.add("active");
    }

async function checkSession() {
    try {
        const response = await fetch("/session", {
            cache: "no-store"
        });

        const user = await response.json();
        const logoutButton = document.getElementById("logout-button");
            if (logoutButton) {
                logoutButton.style.display = "none";
        }

        if (user.logged_in) {
            guestActions.hidden = true;
            guestActions.style.display = "none";

            profileLink.hidden = false;
            profileLink.style.display = "inline-block";

            if (logoutButton) {
                logoutButton.style.display = "inline-block";
            }

        } else {
            guestActions.hidden = false;
            guestActions.style.display = "flex";

            profileLink.hidden = true;
            profileLink.style.display = "none";

            if (logoutButton) {
                logoutButton.style.display = "none";
            }
        }

    } catch (error) {
        console.error("Ошибка проверки авторизации:", error);
    }
}

checkSession()

// Элементы регистрации
const openRegisterButton = document.querySelector("#open-register");
const registerOverlay = document.querySelector("#register-overlay");
const closeRegisterButton = document.querySelector("#close-register");
const openRegisterFromLogin = document.querySelector("#open-register-from-login");
const openLoginFromRegister = document.querySelector("#open-login-from-register");

const registerForm = document.querySelector("#register-form");
const registerMessage = document.querySelector("#register-message");

// Открытие регистрации
function openRegister() {
    overlay.classList.remove("is-open");
    registerOverlay.classList.add("is-open");
}

// Закрытие регистрации
function closeRegister() {
    registerOverlay.classList.remove("is-open");
}

// Переход с входа на регистрацию
if (openRegisterFromLogin) {
    openRegisterFromLogin.addEventListener("click", function (event) {
        event.preventDefault();
        openRegister();
    });
}

// Переход с регистрации на вход
if (openLoginFromRegister) {
    openLoginFromRegister.addEventListener("click", function (event) {
        event.preventDefault();
        registerOverlay.classList.remove("is-open");
        overlay.classList.add("is-open");
    });
}

// Открытие регистрации
if (openRegisterButton) {
    openRegisterButton.addEventListener("click", function (event) {
        event.preventDefault();
        openRegister();
    });
}

// Закрытие регистрации
if (closeRegisterButton) {
    closeRegisterButton.addEventListener("click", closeRegister);
}

// Закрытие по нажатию на затемнение
if (registerOverlay) {
    registerOverlay.addEventListener("click", function (event) {
        if (event.target === registerOverlay) {
            closeRegister();
        }
    });
}

// Отправка регистрации
if (registerForm) {
    registerForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        setMessage(
            registerMessage,
            "Регистрируем пользователя...",
            "info"
        );

        try {
            const response = await fetch("/register", {
                method: "POST",
                body: new URLSearchParams(new FormData(registerForm))
            });

            const message = await response.text();

            if (response.ok) {
                setMessage(registerMessage, message, "success");

                registerForm.reset();
                closeRegister();
                await checkSession();
            } else {
                setMessage(registerMessage, message, "error");
            }

        } catch (error) {
            setMessage(
                registerMessage,
                "Не удалось связаться с сервером.",
                "error"
            );

            console.error("Ошибка регистрации:", error);
        }
    });
}





// ========================================
// ВСПЛЫВАЮЩАЯ КАРТОЧКА ТОВАРА
// ========================================

// Находим элементы HTML
const productModal = document.querySelector("#product-modal");
const productModalClose = document.querySelector(".product-modal-close");
const productModalOverlay = document.querySelector(".product-modal-overlay");
const productModalBody = document.querySelector("#product-modal-body");



// Закрытие карточки товара
function closeProductModal() {
    productModal.classList.remove("active")
}


// Открытие карточки товара
async function openProductModal(productId) {

    // Показывать окно
    productModal.classList.add("active");

    // Сообщение о загрузке
    setMessage(productModalBody, "Загрузка товара...", "info");

    try {
        const response = await fetch(`/api/products/${productId}`);

        if (!response.ok) {
            throw new Error("Не удалось загрузить товар");
        }

        const product = await response.json();

        const specificationsHTML = product.specifications.map(specification => {
            return `
                <div class="specification">
                    <span class="specification-name">${specification.name}</span>
                    <span class="specification-value">${specification.value}</span>
                </div>
            `;
        }).join("");

        productModalBody.innerHTML = `
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

    } catch (error) {
        setMessage(productModalBody, "Не удалось загрузить товар.", "error");

        console.error("Ошибка загрузки товара:", error);
    }
}


// Работа всплывающей карточки товара

if (productModal && productModalClose &&
    productModalOverlay && productModalBody) {

    // Открытие карточки товара
    document.addEventListener("click", function (event) {

        const productElement = event.target.closest(".product-open");

        if (!productElement) {
            return;
        }

        const productId = productElement.dataset.productId;

        openProductModal(productId);
    });

    // Закрытие крестиком
    productModalClose.addEventListener("click", closeProductModal);

    // Закрытие нажатием на затемнённую область
    productModalOverlay.addEventListener("click", closeProductModal);
}


// Кнопка выхода
const logoutButton = document.getElementById("logout-button");

if (logoutButton) {
    logoutButton.addEventListener("click", async function () {

        const response = await fetch("/logout", {
            method: "POST"
        });

        if (response.ok) {
            window.location.href = "index.html";
        } else {
            alert("Не удалось выйти из аккаунта");
        }
    });
}