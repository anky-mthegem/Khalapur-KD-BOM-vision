// Interactive Controller for Industrial SOP & User Manual

document.addEventListener('DOMContentLoaded', () => {
  initSearch();
  initRoleTabs();
  initChecklists();
  initScrollSpy();
});

// 1. Search Filter across SOP Sections
function initSearch() {
  const searchInput = document.getElementById('sopSearch');
  if (!searchInput) return;

  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase().trim();
    const sections = document.querySelectorAll('.sop-section');
    const navItems = document.querySelectorAll('.nav-item');

    sections.forEach((section) => {
      const text = section.innerText.toLowerCase();
      const match = text.includes(query);
      section.style.display = match ? 'block' : 'none';
    });

    navItems.forEach((item) => {
      const targetId = item.getAttribute('data-target');
      const targetSec = document.getElementById(targetId);
      if (targetSec) {
        item.style.display = targetSec.style.display === 'none' ? 'none' : 'block';
      }
    });
  });
}

// 2. Role-Based Navigation Filter (Operator / Supervisor / Engineer)
function initRoleTabs() {
  const roleButtons = document.querySelectorAll('.nav-role-btn');
  roleButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      roleButtons.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');

      const role = btn.getAttribute('data-role');
      filterByRole(role);
    });
  });
}

function filterByRole(role) {
  const sections = document.querySelectorAll('.sop-section');
  sections.forEach((sec) => {
    const roles = sec.getAttribute('data-roles') || 'all';
    if (role === 'all' || roles.includes(role) || roles === 'all') {
      sec.style.display = 'block';
    } else {
      sec.style.display = 'none';
    }
  });

  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach((item) => {
    const targetId = item.getAttribute('data-target');
    const targetSec = document.getElementById(targetId);
    if (targetSec) {
      item.style.display = targetSec.style.display === 'none' ? 'none' : 'block';
    }
  });
}

// 3. Shift Handover Checklists with Local Storage Persistence
function initChecklists() {
  const checkboxes = document.querySelectorAll('.checklist input[type="checkbox"]');
  checkboxes.forEach((cb) => {
    const key = `sop_check_${cb.id}`;
    if (localStorage.getItem(key) === 'true') {
      cb.checked = true;
      cb.parentElement.classList.add('checked');
    }

    cb.addEventListener('change', () => {
      localStorage.setItem(key, cb.checked);
      if (cb.checked) {
        cb.parentElement.classList.add('checked');
      } else {
        cb.parentElement.classList.remove('checked');
      }
    });
  });
}

function resetChecklist() {
  const checkboxes = document.querySelectorAll('.checklist input[type="checkbox"]');
  checkboxes.forEach((cb) => {
    cb.checked = false;
    cb.parentElement.classList.remove('checked');
    localStorage.removeItem(`sop_check_${cb.id}`);
  });
}

// 4. Scrollspy for Active Section
function initScrollSpy() {
  const sections = document.querySelectorAll('.sop-section');
  const navItems = document.querySelectorAll('.nav-item');

  window.addEventListener('scroll', () => {
    let currentId = '';
    const scrollPos = window.scrollY + 100;

    sections.forEach((section) => {
      if (section.style.display !== 'none') {
        const top = section.offsetTop;
        const height = section.offsetHeight;
        if (scrollPos >= top && scrollPos < top + height) {
          currentId = section.getAttribute('id');
        }
      }
    });

    navItems.forEach((item) => {
      item.classList.remove('active');
      if (item.getAttribute('data-target') === currentId) {
        item.classList.add('active');
      }
    });
  });
}

// Global print trigger
function printSOP() {
  window.print();
}
