import React from 'react'

type Props = {
  children: React.ReactNode
}

const MainLayout: React.FC<Props> = ({ children }) => {
  return (
    <div className="min-h-screen bg-black text-white font-sans">
      <header className="w-full py-5 px-6 bg-gradient-to-r from-gray-900 to-gray-800 shadow-md flex justify-between items-center">
        <h1 className="text-2xl font-bold tracking-tight">Q-ALGO Terminal</h1>
        <div className="text-sm text-gray-400">SPY 0DTE Mesh Intelligence</div>
      </header>

      <main className="p-6 max-w-screen-2xl mx-auto">{children}</main>

      <footer className="text-center text-xs text-gray-500 mt-8 py-6 border-t border-gray-800">
        &copy; {new Date().getFullYear()} Q-ALGO. All rights reserved.
      </footer>
    </div>
  )
}

export default MainLayout
