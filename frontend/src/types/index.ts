export interface Product {
  id: number
  name: string
  price: number
  stock: number
  category: string
  description: string
}

export interface User {
  id: number
  username: string
  email: string
  level: string
  balance: number
  role?: 'USER' | 'ADMIN'
}

export interface OrderItem {
  productId: number
  productName?: string
  quantity: number
  price: number
}

export interface Order {
  id: number
  userId: number
  totalAmount: number
  status: string
  items: OrderItem[]
  createdAt?: string
}

export interface CartItem {
  productId: number
  productName: string
  price: number
  quantity: number
}

export interface Payment {
  id: number
  orderId: number
  amount: number
  status: string
  paymentMethod?: string
}
