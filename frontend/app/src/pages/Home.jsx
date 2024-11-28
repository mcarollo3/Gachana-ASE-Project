import React from "react";
import { Box, TextField, Button, Typography, Link } from "@mui/material";
import PersonalArea from "./PersonalArea";
function Home() {
  const [whichForm, setWhichForm] = React.useState("login");
  return (
    <React.Fragment>
      <Typography
        variant="h1"
        sx={{
          fontFamily: '"Fontdiner Swanky", serif',
          fontWeight: 400,
          fontStyle: "normal",
          marginTop: 8,
          fontSize: "8rem",
          textShadow: "3px 3px 3px black",
        }}
      >
        Gachana
      </Typography>
      <Box
        sx={{
          height: "40vh",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <Box
          sx={{
            background: "#FFFFFF",
            width: "400px",
            padding: "20px",
            borderRadius: "16px",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "16px",
            color: "black",
          }}
        >
          {whichForm === "login" && (
            <>
              <Typography variant="h5" component="h1">
                Login
              </Typography>

              <TextField
                id="email"
                label="Email"
                variant="filled"
                type="email"
                fullWidth
                required
              />

              <TextField
                id="password"
                label="Password"
                variant="filled"
                type="password"
                fullWidth
                required
              />

              <Button
                variant="contained"
                color="primary"
                fullWidth
                sx={{ mt: 2 }}
              >
                Login
              </Button>

              <Typography variant="body2">
                Don't have an account?{" "}
                <Link onClick={() => setWhichForm("signup")} underline="hover">
                  Sign up
                </Link>
              </Typography>
            </>
          )}

          {whichForm === "signup" && (
            <>
              <Typography variant="h5" component="h1">
                Sign Up
              </Typography>

              <TextField
                id="username"
                label="Username"
                variant="filled"
                type="text"
                fullWidth
                required
              />

              <TextField
                id="password"
                label="Password"
                variant="filled"
                type="password"
                fullWidth
                required
              />

              <Button
                variant="contained"
                color="primary"
                fullWidth
                sx={{ mt: 2 }}
              >
                Sign Up
              </Button>

              <Typography variant="body2">
                Already have an account?{" "}
                <Link onClick={() => setWhichForm("login")} underline="hover">
                  Log in
                </Link>
              </Typography>
            </>
          )}
        </Box>
      </Box>
    </React.Fragment>
  );
}

export default Home;
