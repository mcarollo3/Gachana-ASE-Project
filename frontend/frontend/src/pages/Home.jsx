import React from "react";
import TextField from "@mui/material/TextField";
import Box from "@mui/material/Box";

function Home() {
  return (
    <React.Fragment>
      <Box sx={{ background: "white" }}>
        <TextField id="outlined-basic" label="Outlined" variant="filled" />
      </Box>
    </React.Fragment>
  );
}

export default Home;
