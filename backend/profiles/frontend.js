/* =========================
   GET ELEMENTS
========================= */

const loginForm = document.getElementById("loginForm");

const username = document.getElementById("username");
const email = document.getElementById("email");
const password = document.getElementById("password");

const usernameError = document.getElementById("usernameError");
const emailError = document.getElementById("emailError");
const passwordError = document.getElementById("passwordError");

const loginMessage = document.getElementById("loginMessage");

const togglePassword = document.getElementById("togglePassword");

const forgotPassword = document.getElementById("forgotPassword");


/* =========================
   USERNAME VALIDATION
========================= */

// Only letters and spaces
const usernamePattern = /^[A-Za-z ]+$/;


/* =========================
   EMAIL VALIDATION
========================= */

// Valid email format
const emailPattern =
    /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;


/* =========================
   PASSWORD VALIDATION
========================= */

// At least:
// 1 uppercase
// 1 lowercase
// 1 number
// 1 special character
// Minimum 8 characters

const passwordPattern =
    /^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[^A-Za-z0-9]).{8,}$/;


/* =========================
   SHOW / HIDE PASSWORD
========================= */

togglePassword.addEventListener("click", function () {

    if (password.type === "password") {

        password.type = "text";

        togglePassword.textContent = "🙈";

        togglePassword.setAttribute(
            "aria-label",
            "Hide password"
        );

    } else {

        password.type = "password";

        togglePassword.textContent = "🙈";

        togglePassword.setAttribute(
            "aria-label",
            "Show password"
        );
    }

});


/* =========================
   FORM SUBMIT
========================= */

loginForm.addEventListener("submit", function (event) {

    event.preventDefault();


    // Clear previous messages

    usernameError.textContent = "";
    emailError.textContent = "";
    passwordError.textContent = "";
    loginMessage.textContent = "";

    let valid = true;


    /* =========================
       USERNAME CHECK
    ========================= */

    const usernameValue = username.value.trim();

    if (usernameValue === "") {

        usernameError.textContent =
            "Username is required.";

        valid = false;

    } else if (!usernamePattern.test(usernameValue)) {

        usernameError.textContent =
            "Username must contain only letters and spaces. Numbers and special characters are not allowed.";

        valid = false;
    }


    /* =========================
       EMAIL CHECK
    ========================= */

    const emailValue = email.value.trim();

    if (emailValue === "") {

        emailError.textContent =
            "Email is required.";

        valid = false;

    } else if (!emailPattern.test(emailValue)) {

        emailError.textContent =
            "Please enter a valid email address.";

        valid = false;
    }


    /* =========================
       PASSWORD CHECK
    ========================= */

    const passwordValue = password.value;

    if (passwordValue === "") {

        passwordError.textContent =
            "Password is required.";

        valid = false;

    } else if (passwordValue.length < 8) {

        passwordError.textContent =
            "Password must contain at least 8 characters.";

        valid = false;

    } else if (!passwordPattern.test(passwordValue)) {

        passwordError.textContent =
            "Password must contain uppercase, lowercase, number and special character.";

        valid = false;
    }


    /* =========================
       LOGIN
    ========================= */

    if (valid) {

        const selectedRole =
            document.querySelector(
                'input[name="role"]:checked'
            ).value;


        loginMessage.style.color = "green";

        loginMessage.textContent =
            "Login details are valid! Role: " +
            selectedRole.toUpperCase();


        /*
           IMPORTANT:

           This only validates the login form.

           For a real project, username/password
           must be checked against your backend/database.

           Do NOT store real passwords directly
           inside JavaScript.
        */

    } else {

        loginMessage.style.color = "#e53935";

        loginMessage.textContent =
            "Please correct the errors above.";
    }

});


/* =========================
   FORGOT PASSWORD
========================= */

forgotPassword.addEventListener("click", function (event) {

    event.preventDefault();

    const emailValue = email.value.trim();

    if (emailValue === "") {

        emailError.textContent =
            "Enter your email address first.";

        email.focus();

        return;
    }

    if (!emailPattern.test(emailValue)) {

        emailError.textContent =
            "Enter a valid email address.";

        email.focus();

        return;
    }

    alert(
        "Password reset instructions will be sent to: " +
        emailValue
    );

});