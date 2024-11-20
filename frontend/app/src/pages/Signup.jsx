import React from "react";
import { Box, TextField, Button, Typography, Link } from "@mui/material";

function Signup() {
  return (
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

      <Button variant="contained" color="primary" fullWidth sx={{ mt: 2 }}>
        Sign Up
      </Button>

      <Typography variant="body2">
        Already have an account?{" "}
        <Link href="/" underline="hover">
          Log in
        </Link>
      </Typography>
    </Box>
  );
}

export default Signup;
