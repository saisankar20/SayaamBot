import ChatApp from "./ChatApp";
import "./index.css";   // make sure Tailwind directives are pulled in

function App() {
  return (
    <main className="h-screen bg-gray-50 flex items-center justify-center">
      <ChatApp />
    </main>
  );
}
export default App;
