import { NavLink, Route, Routes } from "react-router-dom";
import { Brand } from "./components/Brand";
import { CatalogPage } from "./pages/CatalogPage";
import { MovieDetailPage } from "./pages/MovieDetailPage";

function Layout() {
  return (
    <div className="app-shell">
      <header className="site-header">
        <div className="container site-header__inner">
          <Brand />
          <nav aria-label="Navegação principal">
            <NavLink to="/" end>Explorar</NavLink>
          </nav>
          <span className="site-header__tag">Meet me in the Afterglow</span>
        </div>
      </header>

      <Routes>
        <Route path="/" element={<CatalogPage />} />
        <Route path="/filmes/:movieId" element={<MovieDetailPage />} />
        <Route path="*" element={<CatalogPage />} />
      </Routes>

      <footer className="site-footer">
        <div className="container site-footer__inner">
          <Brand />
          <p>Feito para quem sempre quer assistir a mais uma história.</p>
          <span>by Kauanny Barros</span>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return <Layout />;
}
