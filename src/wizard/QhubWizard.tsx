import React from 'react';
import { makeStyles, Theme, createStyles } from '@material-ui/core/styles';
import Stepper from '@material-ui/core/Stepper';
import Step from '@material-ui/core/Step';
import StepLabel from '@material-ui/core/StepLabel';
import Button from '@material-ui/core/Button';
import Typography from '@material-ui/core/Typography';
import WelcomePanel from './components/WelcomePanel';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '100%',
    },
    button: {
      marginLeft: theme.spacing(1),
    },
    center_buttons: {
      justifyContent: 'center',
    },
    instructions: {
      marginTop: theme.spacing(1),
      marginBottom: theme.spacing(1),
    },
  }),
);

/*
 * Define interfaces
 */

interface ProjectFormPropTypes {
  /*
   * project name: string
   * will be displayed as a text field, completely
   * configurable by the user.
   */
  project_name: string;

  /*
   * provider: string;
   * will be a dropdown menu that will be
   * a display of all available options
   */
  provider: string;

  /*
   * ci/cd: string;
   * will also have a dropdown to choose 
   * from different options
   */
  ci_cd: string;

  /*
   * domain: string;
   * TODO: ask chris what this is for
   */
  domain: string; 

}


/*
 * This function contains a collection for the title of the deployment step.
 * Documentation will contain more information on how these are linked together.
 *
 * TODO: Share the view from 'setup users' step to the 'setup groups' step so they can see the relations
 * 
 */ 
function getSteps() {
  return ['General Information', 'Setup Project', '{insert project name} - Authentication Setup', '{ipn} - Users Setup', '{ipn} - Groups Setup', '{provider} Setup', 'Profiles (Optional)'];
}

/*
 * This will eventually become its own mini-function, caching the choices into its state.
 * this allows people to go "back" a step with the settings already populated.
 */
function getStepContent(step: number) {
  switch (step) {
    case 0:
	    return <WelcomePanel />;
    case 1:
      return 'authentiacation setup placeholder';
    case 2:
      return 'This is the bit I really care about!';
    case 3:
      return 'groups table placeholder';
    case 4:
      return 'provider placeholder (build with do)'; 
    case 5:
      return 'profiles setup'; 
    case 6:
	    return 'just keep adding more cases'; 
    default:
      return 'Unknown step';
  }
}

export default function QhubWizard() {
  const classes = useStyles();
  const [activeStep, setActiveStep] = React.useState(0);
  const [skipped, setSkipped] = React.useState(new Set<number>());
  const steps = getSteps();

  const isStepOptional = (step: number) => {
    return step === 6;
  };

  const isStepSkipped = (step: number) => {
    return skipped.has(step);
  };

  const handleNext = () => {
    let newSkipped = skipped;
    if (isStepSkipped(activeStep)) {
      newSkipped = new Set(newSkipped.values());
      newSkipped.delete(activeStep);
    }

    setActiveStep((prevActiveStep) => prevActiveStep + 1);
    setSkipped(newSkipped);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleSkip = () => {
    if (!isStepOptional(activeStep)) {
      // You probably want to guard against something like this,
      // it should never occur unless someone's actively trying to break something.
      throw new Error("You can't skip a step that isn't optional.");
    }

    setActiveStep((prevActiveStep) => prevActiveStep + 1);
    setSkipped((prevSkipped) => {
      const newSkipped = new Set(prevSkipped.values());
      newSkipped.add(activeStep);
      return newSkipped;
    });
  };

  const handleReset = () => {
    setActiveStep(0);
  };

  return (
    <div className={classes.root}>
      <Stepper activeStep={activeStep}>
        {steps.map((label, index) => {
          const stepProps: { completed?: boolean } = {};
          const labelProps: { optional?: React.ReactNode } = {};
          if (isStepOptional(index)) {
            labelProps.optional = <Typography variant="caption">Optional</Typography>;
          }
          if (isStepSkipped(index)) {
            stepProps.completed = false;
          }
          return (
            <Step key={label} {...stepProps}>
              <StepLabel {...labelProps}>{label}</StepLabel>
            </Step>
          );
        })}
      </Stepper>
      <div>
        {activeStep === steps.length ? (
          <div>
            <Typography className={classes.instructions}>
              All steps completed - you&apos;re finished
            </Typography>
            <Button onClick={handleReset} className={classes.button}>
              Reset
            </Button>
          </div>
        ) : (
	   <div>
            <Typography className={classes.instructions}>{getStepContent(activeStep)}</Typography>
          <div className={classes.center_buttons}>
              <Button disabled={activeStep === 0} onClick={handleBack} className={classes.button}>
                Back
              </Button>
              {isStepOptional(activeStep) && (
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleSkip}
                  className={classes.button}
                >
                  Skip
                </Button>
              )}
              <Button
                variant="contained"
                color="primary"
                onClick={handleNext}
                className={classes.button}
              >
                {activeStep === steps.length - 1 ? 'Finish' : 'Next'}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


