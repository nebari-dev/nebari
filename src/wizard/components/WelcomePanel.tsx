import React from 'react';
import Typography from '@material-ui/core/Typography';

export default function WelcomePanel() {
	return(
		<div>
			<Typography variant='h5' align='center'>
				Welcome to the Quansight Hub Deployment Wizard
			</Typography>
			<Typography variant='body1' align='center'>
				The aim of this wizard is to provide an easy to administer deplotment of many services that QHub contains. Currently we support:
				<ul>
					<li>JupyterLab</li>
					<li>JupyterLab + Dask</li>
				</ul>
		         With more support to come in the near future. 
			</Typography>
		</div>
	);
};
