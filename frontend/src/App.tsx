import { BrowserRouter, Link, Route, Routes } from "react-router";
import Cart from "./pages/Cart";
import Login from "./pages/Login";
import OrderList from "./pages/OrderList";
import PostDetail from "./pages/PostDetail";
import PostList from "./pages/PostList";
import ProductList from "./pages/ProductList";

function App() {
    return (
        <BrowserRouter>
            <nav>
                <Link to="/">記事</Link> | <Link to="/products">商品</Link> |{" "}
                <Link to="/cart">カート</Link> |{" "}
                <Link to="/orders">注文履歴</Link> |{" "}
                <Link to="/login">ログイン</Link>
            </nav>
            <Routes>
                <Route path="/" element={<PostList />} />
                <Route path="/posts/:postId" element={<PostDetail />} />
                <Route path="/products" element={<ProductList />} />
                <Route path="/cart" element={<Cart />} />
                <Route path="/orders" element={<OrderList />} />
                <Route path="/login" element={<Login />} />
            </Routes>
        </BrowserRouter>
    );
}

export default App;
