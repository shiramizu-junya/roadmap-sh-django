import { BrowserRouter, Link, Route, Routes } from "react-router";
import PostDetail from "./pages/PostDetail";
import PostList from "./pages/PostList";
import ProductList from "./pages/ProductList";

function App() {
    return (
        <BrowserRouter>
            <nav>
                <Link to="/">記事</Link> | <Link to="/products">商品</Link>
            </nav>
            <Routes>
                <Route path="/" element={<PostList />} />
                <Route path="/posts/:postId" element={<PostDetail />} />
                <Route path="/products" element={<ProductList />} />
            </Routes>
        </BrowserRouter>
    );
}

export default App;
