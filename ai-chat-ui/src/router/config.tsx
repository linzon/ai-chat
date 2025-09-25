
import type { RouteObject } from "react-router-dom";
import NotFound from "../pages/NotFound";
import ChatPage from "../pages/chat/page";

const routes: RouteObject[] = [
  {
    path: "/",
    element: <ChatPage />,
  },
  {
    path: "*",
    element: <NotFound />,
  },
];

export default routes;
