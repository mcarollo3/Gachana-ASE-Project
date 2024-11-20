import {
  Card,
  CardActionArea,
  CardContent,
  Button,
  Typography,
} from "@mui/material";

const ButtonCard = (title, description, onClick) => {
  return (
    <Card sx={{ maxWidth: 345, m: 2 }}>
      <CardActionArea onClick={onClick}>
        <CardContent>
          <Typography gutterBottom variant="h5" component="div">
            {title}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {description}
          </Typography>
        </CardContent>
      </CardActionArea>
      <Button
        variant="contained"
        color="primary"
        sx={{ margin: 2 }}
        onClick={onClick}
      >
        Click Me
      </Button>
    </Card>
  );
};

export default ButtonCard;
