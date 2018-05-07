import HTTP from './http-common';
import {ProgressAtom, FailureAtom, StructuredProgressAtom} from './progress-info';

/**
  This class groups together some methods that are used to manipulate users and other stuff.
 */
class AuthenticationController {

  /**
   * Tries to authenticate with a given username and password.
   * @param {string} username: The username to try and authenticate with.
   * @param {string} password: A password to try and authenticate with (plain-text).
   * @param communicationEvent: A Vue event bus to output progress information on.
   */
  async function authenticateUser(username, password, communicationBus) {
    communicationBus.emit('progress', new ProgressAtom("Authenticating..."));
    let stageCount = 5;
    var currentStage = 0;
    try {
      // Initial stage is to retrieve the login token
      const response = await HTTP.post('v1/auth/token', {username: username, password: password});
      if (response.status !== 200) {
        communicationBus.emit('progress', FailureAtom(`Internal error: bad status code ${response.status}`));
        return;
      }
      // Second stage is to set this in localStorage
      communicationBus.emit('progress', new StructuredProgressAtom('Saving token', ++currentStage, stageCount));
      const token = response.data.token;
      localStorage.setItem('Token', token);
      // Third stage is to test the call
      communicationBus.emit('progress', new StructuredProgressAtom('Testing', ++currentStage, stageCount));
      // Make a call to a test location
      const controlResponse = await(HTTP.get('v1/control/user'));
      if (controlResponse.data.username === username) {
        // Have the right user information
        if (controlResponse.data.is_superuser) {
          this.bus.$emit('authenticationChanged', { authenticated: 'admin' });
        } else if (controlResponse.data.is_staff) {
          this.bus.$emit('authenticationChanged', { authenticated: 'staff' });
        } else {
          this.bus.$emit('authenticationChanged', { authenticated: 'annotator' });
        }
      } else {
        throw new Error("Security issue");
      }

      // TODO: create and authenticate the web-socket


    } catch (error) {
      communicationBus.emit('progress', new FailureAtom(`Problem: ${error}`));
      throw error;
    }
    HTTP.post()
  }

}
