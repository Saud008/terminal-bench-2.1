# Resume-hold gate contract

Each device may carry a `resume_token`, a cached link-layer resume key from a previous connection. If `resume_token` is a non-empty string and `resume_cleared` is `false`, the resume slot is still armed from the previous session and the device is blocked with reason `ineligible_resume_armed`.

If `resume_cleared` is `true`, the resume slot has been cleared by the operator regardless of whatever value `resume_token` still holds, and this gate never blocks the device.

If `resume_token` is an empty string, there is no resume slot to clear and this gate never blocks the device, regardless of `resume_cleared`.
