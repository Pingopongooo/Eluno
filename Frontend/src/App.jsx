import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { LayoutDashboard, PackageSearch, PlusCircle, BellRing } from 'lucide-react';
import Dashboard from './components/Dashboard';
import NewOrderForm from './components/NewOrderForm';
import InventoryScreen from './components/InventoryScreen';
import AlertsLog from './components/AlertsLog';

function App() {
  // Helper function to keep our classNames clean
  const navLinkClasses = ({ isActive }) =>
    `inline-flex items-center px-1 pt-1 text-sm border-b-2 transition-colors ${
      isActive
        ? 'font-bold text-blue-600 border-blue-600' // ACTIVE STATE: Bold, Blue text, Blue underline
        : 'font-medium text-gray-500 border-transparent hover:text-gray-900 hover:border-blue-500' // INACTIVE STATE
    }`;

  return (
    <Router>
      <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
        {/* Navigation Bar */}
        <nav className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <div className="flex-shrink-0 flex items-center space-x-2">
                  <img src="/eluno.png" alt="E" className="h-6 w-auto" />
                  <span className="font-bold text-xl tracking-tight text-gray-900">AI OMS</span>
                </div>
                <div className="hidden sm:ml-8 sm:flex sm:space-x-8">
                  {/* Swapped <Link> for <NavLink> and applied dynamic classes */}
                  <NavLink to="/" className={navLinkClasses}>
                    <LayoutDashboard className="w-4 h-4 mr-2" />
                    Dashboard
                  </NavLink>
                  <NavLink to="/new-order" className={navLinkClasses}>
                    <PlusCircle className="w-4 h-4 mr-2" />
                    New Order
                  </NavLink>
                  <NavLink to="/inventory" className={navLinkClasses}>
                    <PackageSearch className="w-4 h-4 mr-2" />
                    Inventory
                  </NavLink>
                  <NavLink to="/alerts" className={navLinkClasses}>
                    <BellRing className="w-4 h-4 mr-2" />
                    Alerts
                  </NavLink>
                </div>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content Area */}
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/new-order" element={<NewOrderForm />} />
            <Route path="/inventory" element={<InventoryScreen />} />
            <Route path="/alerts" element={<AlertsLog />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
