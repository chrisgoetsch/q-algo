// File: src/components/layout/Sidebar.tsx

import React from 'react';

const links = [
  { label: 'GPT', anchor: 'gpt' },
  { label: 'Mesh', anchor: 'mesh' },
  { label: 'Chart', anchor: 'chart' },
  { label: 'Trades', anchor: 'trades' },
  { label: 'Controls', anchor: 'controls' },
  { label: 'Capital', anchor: 'capital' },
  { label: 'Status', anchor: 'status' },
  { label: 'Learning', anchor: 'learning' },
];

export function Sidebar() {
  return (
    <aside className="w-48 bg-gray-900 text-white p-4 hidden md:block">
      <h1 className="text-xl font-bold mb-6">Q-ALGO</h1>
      <nav className="space-y-2">
        {links.map((link) => (
          <a
            key={link.anchor}
            href={`#${link.anchor}`}
            className="block px-2 py-1 rounded hover:bg-gray-700 transition"
          >
            {link.label}
          </a>
        ))}
      </nav>
    </aside>
  );
}

export default Sidebar;
