import { useState, useEffect } from 'react';
import { fetchLensTypes, createOrder } from '../services/api';
import { useNavigate } from 'react-router-dom';

export default function NewOrderForm() {
  const navigate = useNavigate();
  const [lensTypes, setLensTypes] = useState([]);
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_phone: '',
    store_id: 1, 
    lens_type_id: '',
    lens_index: '',
    coating: '',
    frame_details: '',
    re_sphere: '', re_cylinder: '', re_axis: '', re_add: '',
    le_sphere: '', le_cylinder: '', le_axis: '', le_add: ''
  });

  useEffect(() => {
    fetchLensTypes().then(setLensTypes).catch(console.error);
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Clean up empty strings to send null/numbers properly to FastAPI
    const payload = { ...formData };
    const floatFields = ['re_sphere', 're_cylinder', 're_add', 'le_sphere', 'le_cylinder', 'le_add', 'lens_index'];
    const intFields = ['re_axis', 'le_axis', 'lens_type_id', 'store_id'];

    floatFields.forEach(key => {
      payload[key] = payload[key] === '' ? null : parseFloat(payload[key]);
    });
    intFields.forEach(key => {
      payload[key] = payload[key] === '' ? null : parseInt(payload[key], 10);
    });

    try {
      await createOrder(payload);
      navigate('/'); 
    } catch (error) {
      alert("Failed to create order. Check console.");
      console.error(error);
    }
  };

  return (
    <div className="max-w-4xl mx-auto bg-white p-8 rounded-lg shadow">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Create New Order</h2>
      <form onSubmit={handleSubmit} className="space-y-8">
        
        {/* Customer & Product Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">Customer Name *</label>
            <input type="text" name="customer_name" required onChange={handleChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Phone Number</label>
            <input 
              type="tel" 
              name="customer_phone" 
              pattern="[6-9][0-9]{9}" 
              maxLength="10"
              title="Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9"
              onChange={handleChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500" 
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Lens Type *</label>
            <select name="lens_type_id" required onChange={handleChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500">
              <option value="">Select a lens...</option>
              {lensTypes.map(lens => (
                <option key={lens.id} value={lens.id}>{lens.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Lens Index (e.g. 1.67)</label>
            <input type="number" step="0.01" name="lens_index" onChange={handleChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Coating</label>
            <input type="text" name="coating" placeholder="Anti-Reflective, Scratch-Resistant..." onChange={handleChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Frame Details</label>
            <input type="text" name="frame_details" placeholder="Ray-Ban Aviator Gold..." onChange={handleChange}
              className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500" />
          </div>
        </div>

        {/* Optical Prescription Grid */}
        <div className="border-t border-gray-200 pt-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Prescription Grid</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left border-collapse">
              <thead>
                <tr>
                  <th className="pb-2 font-medium text-gray-500">Eye</th>
                  <th className="pb-2 font-medium text-gray-500 px-2">Sphere (SPH)</th>
                  <th className="pb-2 font-medium text-gray-500 px-2">Cylinder (CYL)</th>
                  <th className="pb-2 font-medium text-gray-500 px-2">Axis</th>
                  <th className="pb-2 font-medium text-gray-500 px-2">Add</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="py-2 font-medium text-gray-900 pr-4">OD (Right)</td>
                  <td className="px-2"><input type="number" step="0.25" name="re_sphere" onChange={handleChange} className="w-full border-gray-300 rounded-md shadow-sm p-2" /></td>
                  <td className="px-2"><input type="number" step="0.25" name="re_cylinder" onChange={handleChange} className="w-full border-gray-300 rounded-md shadow-sm p-2" /></td>
                  <td className="px-2"><input type="number" name="re_axis" onChange={handleChange} className="w-full border-gray-300 rounded-md shadow-sm p-2" /></td>
                  <td className="px-2"><input type="number" step="0.25" name="re_add" onChange={handleChange} className="w-full border-gray-300 rounded-md shadow-sm p-2" /></td>
                </tr>
                <tr>
                  <td className="py-2 font-medium text-gray-900 pr-4">OS (Left)</td>
                  <td className="px-2"><input type="number" step="0.25" name="le_sphere" onChange={handleChange} className="w-full border-gray-300 rounded-md shadow-sm p-2" /></td>
                  <td className="px-2"><input type="number" step="0.25" name="le_cylinder" onChange={handleChange} className="w-full border-gray-300 rounded-md shadow-sm p-2" /></td>
                  <td className="px-2"><input type="number" name="le_axis" onChange={handleChange} className="w-full border-gray-300 rounded-md shadow-sm p-2" /></td>
                  <td className="px-2"><input type="number" step="0.25" name="le_add" onChange={handleChange} className="w-full border-gray-300 rounded-md shadow-sm p-2" /></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <button type="submit" className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
          Submit Order
        </button>
      </form>
    </div>
  );
}