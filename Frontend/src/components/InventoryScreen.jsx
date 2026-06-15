import { useState, useEffect } from 'react';
import { fetchInventory } from '../services/api';

export default function InventoryScreen() {
  const [inventory, setInventory] = useState([]);

  useEffect(() => {
    fetchInventory().then(setInventory).catch(console.error);
  }, []);

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-5 border-b border-gray-200">
        <h3 className="text-lg font-medium text-gray-900">Lens Inventory</h3>
      </div>
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Lens ID</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stock Level</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reorder Threshold</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {inventory.map((item) => (
            <tr key={item.id}>
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">ID: {item.lens_type_id} ({item.lens_type_name})</td>
              {/* FIX: Mapped to item.quantity_in_stock instead of current_stock */}
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.quantity_in_stock}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.reorder_level}</td>
              <td className="px-6 py-4 whitespace-nowrap">
                {item.quantity_in_stock <= item.reorder_level ? (
                  <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">Low Stock</span>
                ) : (
                  <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">Healthy</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}