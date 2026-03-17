const API = "";

const registerForm = document.getElementById("register-form");
const loginForm = document.getElementById("login-form");
const iceCreamForm = document.getElementById("ice-cream-form");
const entryForm = document.getElementById("entry-form");
const tokenEl = document.getElementById("token");
const entriesEl = document.getElementById("entries");
const loadEntriesBtn = document.getElementById("load-entries");

function getToken() {
  return tokenEl.value.trim();
}

async function request(path, options = {}) {
  const res = await fetch(API + path, options);
  const data = await res.json();
  if (!res.ok) {
    const message = data.detail || data.error || "Request failed";
    throw new Error(message);
  }
  return data;
}

registerForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = Object.fromEntries(new FormData(registerForm).entries());
  body.weight = body.weight ? Number(body.weight) : null;
  body.height = body.height ? Number(body.height) : null;
  body.age = body.age ? Number(body.age) : null;

  try {
    await request("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    alert("Регистрация успешна");
  } catch (err) {
    alert(err.message);
  }
});

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = Object.fromEntries(new FormData(loginForm).entries());

  try {
    const data = await request("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    tokenEl.value = data.token;
  } catch (err) {
    alert(err.message);
  }
});

iceCreamForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = Object.fromEntries(new FormData(iceCreamForm).entries());
  body.calories = Number(body.calories);
  body.carbohydrates = Number(body.carbohydrates);
  body.proteins = Number(body.proteins);
  body.fats = Number(body.fats);
  body.sugar = Number(body.sugar);
  body.rysk = Number(body.rysk);

  try {
    await request("/ice-creams", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + getToken(),
      },
      body: JSON.stringify(body),
    });
    alert("Мороженное добавлено");
  } catch (err) {
    alert(err.message);
  }
});

entryForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = Object.fromEntries(new FormData(entryForm).entries());
  body.ice_cream_id = Number(body.ice_cream_id);
  body.amount_grams = Number(body.amount_grams);

  try {
    await request("/entries", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + getToken(),
      },
      body: JSON.stringify(body),
    });
    alert("Запись добавлена");
  } catch (err) {
    alert(err.message);
  }
});

loadEntriesBtn.addEventListener("click", async () => {
  try {
    const data = await request("/entries", {
      headers: { Authorization: "Bearer " + getToken() },
    });
    entriesEl.innerHTML = data
      .map(
        (e) =>
          `<div><strong>${e.ice_cream_name}</strong> — ${e.amount_grams} г, ${e.calories.toFixed(
            1
          )} ккал</div>`
      )
      .join("");
  } catch (err) {
    alert(err.message);
  }
});
