import { fetchFiles, deleteFile, deleteAllFiles, uploadFiles, sendQuery } from './api.js';

fetchFiles().then()

function loader(show=false) {
    if (show) { document.getElementById('loader-wrapper').classList.add('show-loader'); }
    else { document.getElementById('loader-wrapper').classList.remove('show-loader'); }
}

async function loadFileList() {
    loader(true);
    try {
        const files = await fetchFiles();
        const container = document.getElementById('file-list');
        container.innerHTML = '';

        if (files.length === 0) {
            container.classList.add('empty');
            container.innerHTML = '<p class="item">No files</p>';
            loader(false);
            return;
        }

        for (const f of files) {
            const item = document.createElement('div');
            item.setAttribute('data-id', f.file_id);
            item.addEventListener('click', deleteItem);
            item.classList.add('file-item');
            item.classList.add('item');
            item.innerHTML = `
            <span>${f.file}</span>
            <svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg" class="icon"><path d="M14.2548 4.75488C14.5282 4.48152 14.9717 4.48152 15.2451 4.75488C15.5184 5.02825 15.5184 5.47175 15.2451 5.74512L10.9902 10L15.2451 14.2549L15.3349 14.3652C15.514 14.6369 15.4841 15.006 15.2451 15.2451C15.006 15.4842 14.6368 15.5141 14.3652 15.335L14.2548 15.2451L9.99995 10.9902L5.74506 15.2451C5.4717 15.5185 5.0282 15.5185 4.75483 15.2451C4.48146 14.9718 4.48146 14.5282 4.75483 14.2549L9.00971 10L4.75483 5.74512L4.66499 5.63477C4.48589 5.3631 4.51575 4.99396 4.75483 4.75488C4.99391 4.51581 5.36305 4.48594 5.63471 4.66504L5.74506 4.75488L9.99995 9.00977L14.2548 4.75488Z"></path></svg>`;
            container.appendChild(item);
        }
    } catch (err) {
        console.error(err);
        const container = document.getElementById('file-list');
        container.classList.add('empty');
        container.innerHTML = '<p class="item" style="color: #e02e2a;">Error loading</p>';
    }
    loader(false);
}

window.addEventListener('DOMContentLoaded', loadFileList);

// ----- FILE DELETION -----
async function deleteItem(e) {
    loader(true);
    const id = e.target.dataset.id;
    try {
        const res = await deleteFile(id);
        console.log(`Removed ${res.removed_chunks} chunks.`);
        setTimeout(async () => {
            await loadFileList();
            loader(false);
        }, 1200);
    } catch (err) {
        console.error(err);
        alert(`Failed to delete file: ${err.message}`);
        loader(false);
    }
}

document.getElementById('reset-btn').addEventListener('click', deleteAll);
async function deleteAll(e) {
    loader(true);
    const id = e.target.dataset
    try {
        const res = await deleteAllFiles();
        console.log(`${res.status}\nRemoved ${res.chunks_removed} chunks.`);
        setTimeout(async () => {
            await loadFileList();
            loader(false);
        }, 1200);
    } catch (err) {
        console.error(err);
        alert(`Failed to reset: ${err.message}`);
        loader(false);
    }
}

// ----- FILE UPLOAD -----
const merge = (a, b, predicate = (a, b) => a === b) => {
    const c = [...a]; // copy to avoid side effects
    b.forEach((bItem) => (c.some((cItem) => predicate(bItem, cItem)) ? null : c.push(bItem)))
    return c;
}
const file_input = document.getElementById('file-input');
document.getElementById('upload-btn').addEventListener('click', () => {file_input.click()});
file_input.addEventListener('change', async (e) => {
    loader(true);
    const dataTransfer = new DataTransfer();
    let selectedFiles = file_input.files;

    if (selectedFiles.length > 0) {
        if (selectedFiles.length > 5) {
            alert(`We can select a maximum of 5 files (${selectedFiles.length} selected)`);
            selectedFiles = dataTransfer.files;
            loader(false);
            return;
        }
        let errors = {type: [], size: []}
        for (let i = 0; i < selectedFiles.length; i++) {
            const file = selectedFiles[i];
            if (file.type !== 'text/plain' && file.type !== 'text/markdown' && file.type !== 'application/pdf') {
                errors.type.push(file.name);
            }
            else {
                if (file.size > 1024 * 1024) { // 1MB
                    errors.size.push(file.name);
                }
                else {
                    dataTransfer.items.add(file);
                }
            }
        }
        if (errors.type.length > 0 || errors.size.length > 0) {
            const error_files = merge(errors.type, errors.size);
            alert(`Error: Large or unsupported files were selected\n- ${error_files.join(', ')}`);
        }
        if (dataTransfer.files.length > 0) {
            file_input.value = '';
            await uploadFiles(dataTransfer.files);
            setTimeout(async () => {
                await loadFileList();
                loader(false);
            }, 1200);
        }
        else {
            loader(false);
        }
    } else {
        console.log('No files selected.');
        loader(false);
    }
});

// ----- INPUT AREA -----
const userInput = document.getElementById('user-input');
const userInputScollHeight = userInput.scrollHeight;
function autosize(el) {
    setTimeout(function(){
        el.style.height = '';
        if (el.scrollHeight > userInputScollHeight) {
            el.style.height = el.scrollHeight + 'px';
            document.getElementById('input-wrapper').classList.add('expand');
        }
        else {
            document.getElementById('input-wrapper').classList.remove('expand');
        }
    }, 0);
}
userInput.addEventListener('input', (e) => {
    const value = e.target.value;
    if (value.length <= 1) {
        document.getElementById('send-btn').classList.add('disable');
    }
    else if (value.length > 1) {
        document.getElementById('send-btn').classList.remove('disable');
    }
    autosize(e.target);
});
userInput.addEventListener('keydown', function(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    sendBtn.click();
  }
});


// ----- QUERY -----
const sendBtn = document.getElementById('send-btn');
sendBtn.addEventListener('click', sendMessage);

export function sanitizeInput(input) {
  if (!input) return '';
  // Remove invisible control characters
  input = input.replace(/[\x00-\x1F\x7F]/g, '');
  // Escape HTML special chars
  input = input
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/'/g, '&quot;')
    .replace(/'/g, '&#x27;');
  // Trim and truncate if too long
  return input.trim().slice(0, 1024);
}


async function sendMessage() {
    const query = sanitizeInput(userInput.value);
    if (!query || query.length < 2 || query.length > 1024) return;

    userInput.value = '';
    autosize(document.getElementById('user-input'));
    userInput.disabled = true;
    sendBtn.classList.add('disable');
    appendMessage('user', query);
    const agent_msg = appendMessage('agent', 'Thinking...');

    document.getElementById('intro-wrapper').style.display = 'none';

    try {
        const data = await sendQuery(query);
        if (data.answer) {
            const answer = marked.parse(data.answer);
            let citations = '';
            if (data.citations?.length) {
                const refs = data.citations.map(c => {
                    return `<div class="citation">[${c.id}]<div class="cite-text">${c.text}</div></div>`;
                }).join(', ');
                citations += `<p><b>Sources:</b></p><div>${refs}</div>`;
            }
            const response = `${answer}${(citations.length > 0) ? '<br/><br/>'+marked.parse(citations) : ''}`;
            agent_msg.innerHTML = response;
            const container = document.getElementById('chat-log');
            container.scrollTop = container.scrollHeight;
        } else {
            agent_msg.innerHTML = 'no answer';
            console.log('no answer');
        }
    } catch (err) {
        console.error(err);
        agent_msg.innerHTML = err.message;
    } finally {
        userInput.disabled = false;
    }
}

function appendMessage(role='user', msg) {
    const container = document.getElementById('chat-log');
    const item = document.createElement('div');
    if (role === 'user') {
        item.classList.add('user-msg');
    }
    else {
        item.classList.add('agent-msg');
    }
    item.innerHTML = marked.parse(msg);
    container.appendChild(item);
    container.scrollTop = container.scrollHeight;
    return item;
}