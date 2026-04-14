import { mount } from 'svelte'
import App from './App.svelte'

// Global error handler
window.onerror = function (message, source, lineno, colno, error) {
  const errDiv = document.createElement('div');
  errDiv.style.position = 'fixed';
  errDiv.style.top = '0';
  errDiv.style.left = '0';
  errDiv.style.width = '100%';
  errDiv.style.background = '#fee2e2';
  errDiv.style.color = '#991b1b';
  errDiv.style.padding = '20px';
  errDiv.style.zIndex = '999999';
  errDiv.style.borderBottom = '2px solid #7f1d1d';
  errDiv.innerHTML = `<strong>Error:</strong> ${message}<br><small>${source}:${lineno}:${colno}</small><pre>${error?.stack || ''}</pre>`;
  document.body.appendChild(errDiv);
};

window.onunhandledrejection = function (event) {
  const errDiv = document.createElement('div');
  errDiv.innerHTML += `<br><strong>Unhandled Rejection:</strong> ${event.reason}`;
  document.body.prepend(errDiv);
};

const app = mount(App, {
  target: document.getElementById('app'),
})

export default app
