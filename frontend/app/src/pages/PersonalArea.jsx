import ButtonCard from "../components/ButtonCard";

const App = () => {
  const handleCardClick = () => {
    alert("Card clicked!");
  };

  return (
    <div
      style={{ display: "flex", flexWrap: "wrap", justifyContent: "center" }}
    >
      <ButtonCard
        title="Card 1"
        description="This is the first card."
        onClick={handleCardClick}
      />
      <ButtonCard
        title="Card 2"
        description="This is the second card."
        onClick={handleCardClick}
      />
    </div>
  );
};

export default App;
