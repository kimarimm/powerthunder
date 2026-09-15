/**
 * Клиентское приложение - Файловое хранилище
 * SPA с межстраничной навигацией
 */

const API_BASE = '';

// Состояние
let token = localStorage.getItem('token');
let tokenRefreshInterval = null;
const REFRESH_INTERVAL_MS = 25 * 60 * 1000;  // каждые 25 минут

// Элементы
const pages = {
  login: document.getElementById('page-login'),
  register: document.getElementById('page-register'),
  files: document.getElementById('page-files'),
};
const userInfo = document.getElementById('user-info');
const logoutBtn = document.getElementById('logout-btn');
const filesList = document.getElementById('files-list');
const filesEmpty = document.getElementById('files-empty');
const fileInput = document.getElementById('file-input');
const searchInput = document.getElementById('search-input');
const toast = document.getElementById('toast');

// API helpers
async function api(url, options = {}, _retried = false) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(API_BASE + url, { ...options, headers });
  // При 401 — пробуем обновить токен и повторить один раз
  if (res.status === 401 && !_retried && token) {
    const ok = await refreshToken();
    if (ok) return api(url, options, true);
  }
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch (_) {}
  if (!res.ok) throw new Error(data?.detail || res.statusText);
  return data;
}

async function apiFormData(url, formData) {
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(API_BASE + url, {
    method: 'POST',
    headers,
    body: formData,
  });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch (_) {}
  if (!res.ok) throw new Error(data?.detail || res.statusText);
  return data;
}

// Toast
function showToast(message, isError = false) {
  toast.textContent = message;
  toast.className = 'toast show' + (isError ? ' error' : '');
  setTimeout(() => toast.classList.remove('show'), 3000);
}

// Навигация
function showPage(name) {
  Object.values(pages).forEach(p => p?.classList.remove('active'));
  const page = pages[name];
  if (page) page.classList.add('active');

  if (name === 'files') loadFiles(true);
}

function getHashPage() {
  const hash = window.location.hash.slice(1) || '/';
  if (hash === '/' || hash === '/files') return 'files';
  if (hash === '/login') return 'login';
  if (hash === '/register') return 'register';
  return 'files';
}

function updateNav() {
  if (token) {
    logoutBtn.style.display = 'inline-block';
    userInfo.textContent = '';
  } else {
    logoutBtn.style.display = 'none';
    userInfo.textContent = '';
  }
}

// Auth
function onLogin(data) {
  token = data.access_token;
  localStorage.setItem('token', token);
  updateNav();
  startTokenRefresh();
  showPage('files');
  showToast('Вход выполнен');
}

function onLogout() {
  token = null;
  localStorage.removeItem('token');
  stopTokenRefresh();
  updateNav();
  showPage('login');
  showToast('Выход выполнен');
}

async function refreshToken() {
  if (!token) return false;
  try {
    const res = await fetch(API_BASE + '/api/auth/refresh', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      onLogout();
      return false;
    }
    const data = await res.json();
    token = data.access_token;
    localStorage.setItem('token', token);
    return true;
  } catch (_) {
    onLogout();
    return false;
  }
}

function startTokenRefresh() {
  stopTokenRefresh();
  if (!token) return;
  refreshToken();  // сразу обновить при старте
  tokenRefreshInterval = setInterval(refreshToken, REFRESH_INTERVAL_MS);
}

function stopTokenRefresh() {
  if (tokenRefreshInterval) {
    clearInterval(tokenRefreshInterval);
    tokenRefreshInterval = null;
  }
}

let folderTree = [];
let currentFolderId = null;
let folderPathStack = [];

async function loadFiles(resetNav = false) {
  if (!token) return;
  try {
    const data = await api('/api/folders');
    folderTree = data.items || [];
    if (resetNav) {
      currentFolderId = null;
      folderPathStack = [];
    }
    renderGrid();
  } catch (e) {
    showToast(e.message, true);
  }
}

function getCurrentItems() {
  if (!currentFolderId) return folderTree;
  function find(items) {
    for (const item of items) {
      if (item.type === 'folder' && item.id === currentFolderId) return item.children || [];
      if (item.type === 'folder' && item.children) {
        const found = find(item.children);
        if (found) return found;
      }
    }
    return null;
  }
  return find(folderTree) || [];
}

function getFileIconClass() {
  return '';
}

function truncateName(name, maxLen = 18) {
  if (!name || name.length <= maxLen) return name;
  return name.slice(0, maxLen - 3) + '...';
}

function filterItemsBySearch(items, query) {
  if (!query) return items;
  return items.filter(item => item.name.toLowerCase().includes(query));
}

function renderGrid() {
  let items = getCurrentItems();
  items = filterItemsBySearch(items, searchQuery);
  const breadcrumb = document.getElementById('files-breadcrumb');
  if (breadcrumb) {
    breadcrumb.style.display = 'flex';
    breadcrumb.innerHTML = '';

    // Кнопка «Главная» — всегда первая
    const homeSpan = document.createElement('span');
    homeSpan.className = currentFolderId ? 'breadcrumb-link' : 'breadcrumb-current';
    homeSpan.textContent = 'Главная';
    if (currentFolderId) {
      homeSpan.addEventListener('click', () => {
        currentFolderId = null;
        folderPathStack = [];
        renderGrid();
      });
    }
    breadcrumb.appendChild(homeSpan);

    if (currentFolderId) {
      const path = buildFolderPath(currentFolderId);
      path.forEach((seg, idx) => {
        const sep = document.createElement('span');
        sep.className = 'breadcrumb-sep';
        sep.textContent = '/';
        breadcrumb.appendChild(sep);

        const isLast = idx === path.length - 1;
        const span = document.createElement('span');
        span.className = isLast ? 'breadcrumb-current' : 'breadcrumb-link';
        span.textContent = seg.name;

        if (!isLast) {
          span.addEventListener('click', () => {
            const parents = path.slice(0, idx);
            folderPathStack = [null, ...parents.map(p => p.id)];
            currentFolderId = seg.id;
            renderGrid();
          });
        }

        breadcrumb.appendChild(span);
      });
    }
  }
  filesList.innerHTML = '';
  if (items.length === 0) {
    filesEmpty.style.display = 'block';
    filesList.className = 'files-grid-tiles';
    return;
  }
  filesEmpty.style.display = 'none';
  filesList.className = 'files-grid-tiles';
  items.forEach(item => {
    const tile = document.createElement('div');
    tile.className = item.type === 'folder' ? 'grid-tile grid-tile-folder' : 'grid-tile grid-tile-file';
    const iconClass = item.type === 'file' ? getFileIconClass(item.name, item.content_type) : '';
    const iconDiv = item.type === 'folder'
      ? '<div class="grid-tile-icon folder-icon"></div>'
      : `<div class="grid-tile-icon file-icon ${iconClass}"></div>`;

    tile.innerHTML = `
      ${iconDiv}
      <div class="grid-tile-label" title="${escapeHtml(item.name)}">${escapeHtml(truncateName(item.name))}</div>
      <button class="tile-menu-btn" type="button">&#8942;</button>
      <div class="tile-menu" style="display:none">
        ${item.type === 'folder'
          ? `<a href="${API_BASE}/api/folders/${item.id}/download" class="tile-menu-item download-folder" download="${escapeHtml(item.name)}.zip">Скачать ZIP</a>`
          : `<a href="${API_BASE}/api/files/${item.id}/download" class="tile-menu-item" download="${escapeHtml(item.name)}">Скачать</a>`}
        <button class="tile-menu-item tile-menu-delete" type="button">Удалить</button>
      </div>
    `;

    // Три точки — открыть/закрыть меню
    const menuBtn = tile.querySelector('.tile-menu-btn');
    const menu = tile.querySelector('.tile-menu');
    menuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      closeAllMenus();
      menu.style.display = menu.style.display === 'none' ? 'flex' : 'none';
    });

    // Удалить
    tile.querySelector('.tile-menu-delete')?.addEventListener('click', (e) => {
      e.stopPropagation();
      menu.style.display = 'none';
      if (item.type === 'folder') deleteFolder(item.id);
      else deleteFile(item.id);
    });

    // Клик по плитке — папка: открыть; файл (двойной клик): скачать
    if (item.type === 'folder') {
      tile.addEventListener('click', (e) => {
        if (!e.target.closest('.tile-menu-btn') && !e.target.closest('.tile-menu')) {
          folderPathStack.push(currentFolderId);
          currentFolderId = item.id;
          renderGrid();
        }
      });
    } else {
      tile.addEventListener('dblclick', (e) => {
        if (e.target.closest('.tile-menu-btn') || e.target.closest('.tile-menu')) return;
        downloadFile(item.id, item.name);
      });
    }

    filesList.appendChild(tile);
  });
}

function closeAllMenus() {
  document.querySelectorAll('.tile-menu').forEach(m => m.style.display = 'none');
}
document.addEventListener('click', closeAllMenus);

function findFolderById(items, id) {
  for (const item of items) {
    if (item.type === 'folder' && item.id === id) return item;
    if (item.type === 'folder' && item.children?.length) {
      const found = findFolderById(item.children, id);
      if (found) return found;
    }
  }
  return null;
}

// Построить путь от корня до папки с id
function buildFolderPath(targetId) {
  const path = [];
  function search(items, trail) {
    for (const item of items) {
      if (item.type !== 'folder') continue;
      const current = [...trail, { id: item.id, name: item.name }];
      if (item.id === targetId) {
        path.push(...current);
        return true;
      }
      if (item.children?.length && search(item.children, current)) return true;
    }
    return false;
  }
  search(folderTree, []);
  return path;
}


function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}

function downloadFile(id, name) {
  fetch(API_BASE + `/api/files/${id}/download`, {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then(r => {
      if (!r.ok) throw new Error('Ошибка загрузки');
      return r.blob();
    })
    .then(blob => {
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = name || 'file';
      link.click();
      URL.revokeObjectURL(url);
    })
    .catch(err => showToast(err.message, true));
}

async function deleteFile(id) {
  if (!confirm('Удалить файл?')) return;
  try {
    await api(`/api/files/${id}`, { method: 'DELETE' });
    showToast('Файл удалён');
    loadFiles();
  } catch (e) {
    showToast(e.message, true);
  }
}

async function deleteFolder(id) {
  if (!confirm('Удалить папку и все файлы внутри?')) return;
  try {
    await api(`/api/folders/${id}`, { method: 'DELETE' });
    showToast('Папка удалена');
    loadFiles();
  } catch (e) {
    showToast(e.message, true);
  }
}

// Handlers
document.getElementById('login-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    const data = await api('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        username: fd.get('username'),
        password: fd.get('password'),
      }),
    });
    onLogin(data);
  } catch (err) {
    showToast(err.message, true);
  }
});

document.getElementById('register-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    await api('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        username: fd.get('username'),
        email: fd.get('email'),
        password: fd.get('password'),
      }),
    });
    showToast('Регистрация успешна. Войдите.');
    window.location.hash = '#/login';
  } catch (err) {
    showToast(err.message, true);
  }
});

// Upload helpers — загрузка прямо со страницы файлов

async function uploadFiles(fileList) {
  if (!fileList || fileList.length === 0) return;
  try {
    // Проверяем: это массив обёрток {file, path} или простых File?
    const isWrapped = fileList[0] && typeof fileList[0] === 'object' && fileList[0].file instanceof Blob;
    const isSinglePlainFile = !isWrapped && fileList.length === 1 && fileList[0] instanceof Blob;

    if (isSinglePlainFile) {
      // Одиночный файл
      const fd = new FormData();
      fd.append('file', fileList[0]);
      if (currentFolderId) fd.append('folder_id', String(currentFolderId));
      await apiFormData('/api/files', fd);
      showToast('Файл загружен');
    } else {
      // Несколько файлов или папка
      const fd = new FormData();
      fileList.forEach(item => {
        if (isWrapped) {
          fd.append('files', item.file, item.path || item.file.name);
        } else {
          fd.append('files', item, item.name);
        }
      });
      if (currentFolderId) fd.append('parent_id', String(currentFolderId));
      await apiFormData('/api/folders/upload', fd);
      showToast('Загружено');
    }
    loadFiles();
  } catch (err) {
    showToast(err.message, true);
  }
}

// Traverse filesystem entries (for drag-and-drop of folders)
async function traverseEntry(entry, path = '') {
  try {
    if (entry.isFile) {
      const f = await new Promise((resolve, reject) => {
        entry.file(resolve, reject);
      });
      return [{ file: f, path: path + f.name }];
    }
    if (entry.isDirectory) {
      const dir = entry;
      const readAll = async (reader) => {
        let all = [];
        let batch;
        do {
          batch = await new Promise((resolve, reject) => reader.readEntries(resolve, reject));
          all = all.concat(batch);
        } while (batch.length > 0);
        return all;
      };
      const children = await readAll(dir.createReader());
      let result = [];
      for (const child of children) {
        result = result.concat(await traverseEntry(child, path + dir.name + '/'));
      }
      return result;
    }
  } catch (err) {
    console.warn('traverseEntry error:', err);
  }
  return [];
}

// Upload button (выбор через диалог)
document.getElementById('upload-trigger-btn')?.addEventListener('click', () => fileInput?.click());

fileInput?.addEventListener('change', () => {
  const files = fileInput.files;
  if (!files?.length) return;
  const hasPaths = files[0]?.webkitRelativePath;
  if (files.length === 1 && !hasPaths) {
    uploadFiles([files[0]]);
  } else {
    const items = [...files].map(f => ({
      file: f,
      path: (f.webkitRelativePath || f.name).replace(/\\/g, '/'),
    }));
    uploadFiles(items);
  }
  fileInput.value = '';
});

// Page-level drag-and-drop
let pageDragCounter = 0;
let pageDropOverlay = null;

function showDropOverlay() {
  if (pageDropOverlay) return;
  pageDropOverlay = document.createElement('div');
  pageDropOverlay.className = 'page-drop-overlay';
  pageDropOverlay.innerHTML = '<span>Отпустите для загрузки</span>';
  document.body.appendChild(pageDropOverlay);
}

function hideDropOverlay() {
  if (pageDropOverlay) {
    pageDropOverlay.remove();
    pageDropOverlay = null;
  }
}

document.addEventListener('dragenter', (e) => {
  if (!token || !pages.files?.classList.contains('active')) return;
  e.preventDefault();
  pageDragCounter++;
  if (pageDragCounter === 1) showDropOverlay();
});

document.addEventListener('dragleave', (e) => {
  if (!token) return;
  e.preventDefault();
  pageDragCounter--;
  if (pageDragCounter <= 0) {
    pageDragCounter = 0;
    hideDropOverlay();
  }
});

document.addEventListener('dragover', (e) => {
  if (!token || !pages.files?.classList.contains('active')) return;
  e.preventDefault();
});

document.addEventListener('drop', (e) => {
  if (!token || !pages.files?.classList.contains('active')) return;
  e.preventDefault();
  pageDragCounter = 0;
  hideDropOverlay();

  // Сохраняем ссылки синхронно до любых async-операций
  const dtItems = e.dataTransfer?.items;
  const dtFiles = e.dataTransfer?.files;
  const filesCopy = dtFiles?.length ? [...dtFiles] : [];

  // Пытаемся через webkitGetAsEntry (поддержка папок)
  if (dtItems?.length) {
    const entries = [...dtItems]
      .map(i => (typeof i.webkitGetAsEntry === 'function') ? i.webkitGetAsEntry() : null)
      .filter(Boolean);

    if (entries.length > 0) {
      Promise.all(entries.map(en => traverseEntry(en)))
        .then(results => {
          const flat = results.flat();
          if (flat.length > 0) {
            uploadFiles(flat);
          } else if (filesCopy.length > 0) {
            uploadFiles(filesCopy);
          }
        })
        .catch(() => {
          // Фоллбэк на простые файлы при ошибке
          if (filesCopy.length > 0) uploadFiles(filesCopy);
        });
      return;
    }
  }

  // Фоллбэк: простые файлы
  if (filesCopy.length > 0) {
    uploadFiles(filesCopy);
  }
});

// Search / filter
let searchQuery = '';
searchInput?.addEventListener('input', () => {
  searchQuery = searchInput.value.trim().toLowerCase();
  renderGrid();
});

// Create folder
const createFolderBtn = document.getElementById('create-folder-btn');
const createFolderForm = document.getElementById('create-folder-form');
const folderNameInput = document.getElementById('folder-name-input');
const createFolderSubmit = document.getElementById('create-folder-submit');
const createFolderCancel = document.getElementById('create-folder-cancel');

createFolderBtn?.addEventListener('click', () => {
  createFolderForm.style.display = 'flex';
  folderNameInput?.focus();
});
createFolderCancel?.addEventListener('click', () => {
  createFolderForm.style.display = 'none';
  folderNameInput.value = '';
});
createFolderSubmit?.addEventListener('click', async () => {
  const name = folderNameInput?.value?.trim();
  if (!name) return;
  try {
    const fd = new FormData();
    fd.append('name', name);
    if (currentFolderId) fd.append('parent_id', String(currentFolderId));
    const res = await fetch(API_BASE + '/api/folders', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: fd,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Ошибка');
    }
    showToast('Папка создана');
    createFolderForm.style.display = 'none';
    folderNameInput.value = '';
    loadFiles();
  } catch (e) {
    showToast(e.message, true);
  }
});


// Download with auth (files and folder zip)
document.addEventListener('click', (e) => {
  const a = e.target.closest('a[download]');
  if (a && (a.href?.includes('/download') || a.classList.contains('download-folder'))) {
    e.preventDefault();
    fetch(a.href, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => {
        if (!r.ok) throw new Error('Ошибка загрузки');
        return r.blob();
      })
      .then(blob => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = a.download || 'file';
        link.click();
        URL.revokeObjectURL(url);
      })
      .catch(err => showToast(err.message, true));
  }
});

logoutBtn?.addEventListener('click', onLogout);

// Hash routing
window.addEventListener('hashchange', () => {
  const page = getHashPage();
  if (token) {
    if (page === 'login' || page === 'register') showPage('files');
    else showPage(page);
  } else {
    if (page === 'files') showPage('login');
    else showPage(page);
  }
});

// Init
updateNav();
if (token) startTokenRefresh();
const page = getHashPage();
if (token) {
  if (page === 'login' || page === 'register') showPage('files');
  else showPage(page);
} else {
  if (page === 'files') showPage('login');
  else showPage(page);
}
