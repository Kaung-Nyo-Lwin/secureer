"use strict";

document.querySelectorAll("[data-enhanced]").forEach((element) => {
  element.hidden = false;
});

const skillsInput = document.getElementById("id_skills");
const skillButtons = document.querySelectorAll("[data-skill]");
const parseSkills = () => skillsInput.value.split(/[,;\n]/).map((value) => value.trim()).filter(Boolean);
const refreshSuggestions = () => {
  if (!skillsInput) return;
  const selected = parseSkills().map((skill) => skill.toLowerCase());
  skillButtons.forEach((button) => {
    const active = selected.includes(button.dataset.skill.toLowerCase());
    button.setAttribute("aria-pressed", String(active));
    button.textContent = `${active ? "✓" : "+"} ${button.dataset.skill}`;
  });
};
skillButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const skills = parseSkills();
    const index = skills.findIndex((skill) => skill.toLowerCase() === button.dataset.skill.toLowerCase());
    if (index >= 0) skills.splice(index, 1);
    else skills.push(button.dataset.skill);
    skillsInput.value = skills.join(", ");
    refreshSuggestions();
    skillsInput.focus();
  });
});
skillsInput?.addEventListener("input", refreshSuggestions);
refreshSuggestions();

const form = document.getElementById("assessment-form");
form?.addEventListener("submit", () => {
  const button = document.getElementById("submit-assessment");
  button.disabled = true;
  button.querySelector("span").textContent = "Exploring your possibilities…";
  document.getElementById("loading-message").hidden = false;
  form.setAttribute("aria-busy", "true");
});

// Browsers can restore the disabled submit button when navigating back.
window.addEventListener("pageshow", () => {
  if (!form) return;
  const button = document.getElementById("submit-assessment");
  button.disabled = false;
  button.querySelector("span").textContent = "Explore my career";
  document.getElementById("loading-message").hidden = true;
  form.removeAttribute("aria-busy");
});

document.querySelector("[data-print]")?.addEventListener("click", () => window.print());
document.getElementById("form-errors")?.focus();
