const API_BASE = import.meta.env.VITE_API_BASE_URL;

export const fetchOrders = async () => {
    const response = await fetch(`${API_BASE}/api/orders`);
    if (!response.ok) throw new Error("Failed to fetch orders");
    return response.json();
};

export const fetchInventory = async () => {
    const response = await fetch(`${API_BASE}/api/inventory`);
    if (!response.ok) throw new Error("Failed to fetch inventory");
    return response.json();
};

export const fetchLensTypes = async () => {
    const response = await fetch(`${API_BASE}/api/lens-types`);
    if (!response.ok) throw new Error("Failed to fetch lens types");
    return response.json();
};

export const createOrder = async (orderData) => {
    const response = await fetch(`${API_BASE}/api/orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(orderData),
    });
    if (!response.ok) throw new Error("Failed to create order");
    return response.json();
};

export const updateOrderStatus = async (orderId, statusData) => {
    const response = await fetch(`${API_BASE}/api/orders/${orderId}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(statusData),
    });
    if (!response.ok) throw new Error("Failed to update status");
    return response.json();
};

export const markQCFailed = async (orderId, statusData) => {
    const response = await fetch(`${API_BASE}/api/orders/${orderId}/qc-fail`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(statusData),
    });
    if (!response.ok) throw new Error("Failed to mark QC Failed");
    return response.json();
};

export const fetchOrderHistory = async (orderId) => {
    const response = await fetch(`${API_BASE}/api/orders/${orderId}/history`);
    if (!response.ok) throw new Error("Failed to fetch order history");
    return response.json();
};

export const fetchAlerts = async () => {
    const response = await fetch(`${API_BASE}/api/alerts`);
    if (!response.ok) throw new Error("Failed to fetch alerts");
    return response.json();
};

export const deleteOrder = async (orderId) => {
    const response = await fetch(`${API_BASE}/api/orders/${orderId}`, {
        method: "DELETE",
    });
    if (!response.ok) throw new Error("Failed to delete order");
    return response.json();
};
