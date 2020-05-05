import React from 'react';
import { Theme, createStyles, makeStyles } from '@material-ui/core/styles';
import { Container, Paper, Typography, Grid, TextField } from '@material-ui/core';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
	flexGrow: 1,
	},
    paper: {
        margin: theme.spacing(1),
	padding: theme.spacing(2),
	width: theme.spacing(64),
	height: theme.spacing(64),
    },
  }),
);



export default function ProjectSetupForm() {
  const classes = useStyles();

  return (
   <div className={classes.root}>
	   <Grid container spacing={3} alignItems='center'>
		<Grid item xs={12}>
		<Typography variant='h4' align='right'> Let's get started! </Typography>
	</Grid>
		<Grid item xs={6} direction="row" >
		<Paper elevation={9} className={classes.paper}>  
			<Grid container spacing={3}>
				<Grid item xs={6}>
					<Typography variant='body1' align='center'> Project Name </Typography>
				</Grid>
				<Grid item xs={6}>
				<TextField />
				</Grid>
			</Grid>
		</Paper>
	</Grid>
	</Grid>
   </div>
  );
}
