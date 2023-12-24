# TST Utils

This project contains some helpers to parse a trade republic tst file (pdf report) and use the output data to fill in the belgian TST file that should be sent to state.

This code-base is purely opportunistic, and will rely on the simplest tools it can find to reach its goal.  Consistency of the technology used is not the primary goal, having a solution that works is.

## Parsing Trade Republic transaction report

This is done in python, using pypdf and some naive regexes.  There is no guarantee it will continue to work in the future.

See [tr-report-parser](./tr-report-parser/).

## Filling in TST form

This one is written in Javascript, and runs with node, inside a podman container.  The tool relies on the pdf-lib library, it is highly dependant on the form file used, and has only been tested with https://finance.belgium.be/sites/default/files/Changement%20de%20compte%20formulaire%20TST%20EN.pdf

See [tst-filler](./tst-filler/).

## Send TST form

This one is written in python, using gmail api to prepare a draft email, that can be sent to the belgian administration.  The tst form filled is attached to the email.

See [tst-sender](./tst-sender/).
