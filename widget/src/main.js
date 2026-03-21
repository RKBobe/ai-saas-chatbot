import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles.css';

// This function can be called from any website to embed the widget
window.initChatbot = (containerId) => {
  const container = document.getElementById(containerId);
  if (container) {
    const root = ReactDOM.createRoot(container);
    root.render(
      <React.StrictMode>
        <App />
      </React.StrictMode>
    );
  } else {
    console.error(`Container #${containerId} not found.`);
  }
};
