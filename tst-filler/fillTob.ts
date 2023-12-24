import { PDFDocument, PDFPage } from 'pdf-lib';
import { readFile, writeFile } from 'fs/promises';
import { readFileSync } from 'fs';
import { program } from 'commander';


// Dictionary saving the position of the input lines for the different
// types of taxed products (without upper limit only)
const taxProductsPositions = {
    0.12: { x: 225, y: 539 },
    0.35: { x: 225, y: 458 },
    1.32: { x: 225, y: 434 },
}


interface TaxPerson {
    /** Object representing a belgian person, paying TST taxes. */

    fullName: string;
    /** The full name of the citizen */

    nationalRegisterNumber: string;
    /** The national register number for this citizen */

    address: string[];
    /** The official address for this citizen */
}

interface TaxProduct {
    /** Object representing a type of assets the citizen needs pay the tax on */

    stockTax: number;
    /** The percentage of tax applied to this type of assets */

    transactionCount: number;
    /** The total amount of transactions done this month for this type of assets */

    taxBasis: number;
    /** The total amount of money spent on that type of assets */

    taxAmount: number;
    /** The total amount of tax to pay to the state for this type of assets (taxBasis * stockTax) */
}

interface TaxData {
    /** Object representing a tax report made by a citizen, about different tax products */

    month: number;
    /** The month at which all the products have been bought */

    year: number;
    /** The year at which the products have been bought */

    products: TaxProduct[];
    /** The list of products bought */
}


/**
 * Draw a big number on the given page, following the template of the Belgian TST doc.
 * The number should be separated every three digits, and for its decimals.
 * It will be printed out as XXX XXX XXX .YY (in the document, the comma separation
 * belongs in between X and Y).
 * 
 * @param page The page to print the big number on.
 * @param value The number value to evaluate and print
 * @param position The position of the comma, around which the number should be printed
 * @param size The desired size for the printed text
 */
async function drawBigNumber(page: PDFPage, value: number, position: { x: number, y: number }, size: number) {
    // Write millions euros
    if (value > 999999) {
        page.drawText(`${Math.floor(value / 1000000)}`, {
            x: position.x - 100,
            y: position.y,
            size: size,
        });
        value = value % 1000000;
    }

    // Write thousands euros
    if (value > 999) {
        page.drawText(`${Math.floor(value / 1000)}`, {
            x: position.x - 65,
            y: position.y,
            size: size,
        });
        value = value % 1000;
    }

    // Write euros
    if (value > 0.99) {
        page.drawText(`${Math.floor(value)}`, {
            x: position.x - 30,
            y: position.y,
            size: size,
        });
        value = value % 1;
    } else {
        page.drawText(`0`, {
            x: position.x - 10,
            y: position.y,
            size: size,
        });
    }

    // Write cents
    if (value >= 0.1) {
        page.drawText(`.${Math.round(value * 100)}`, {
            x: position.x - 2,
            y: position.y,
            size: size,
        })
    } else if (value >= 0.01) {
        page.drawText(`.0${Math.round(value * 100)}`, {
            x: position.x - 2,
            y: position.y,
            size: size,
        })
    } else {
        page.drawText(`.00`, {
            x: position.x - 2,
            y: position.y,
            size: size,
        })
    }
}


/**
 * Fillin all personal information in the TST document.
 * 
 * @param doc The document file
 * @param taxPerson The citizen filling in the document
 * @param signatureLocation The place where the current document is being signed from
 * @param signatureFile The picture file, containing the actual signature of the citizen
 */
async function fillInPersonalInfo(
    doc: PDFDocument,
    taxPerson: TaxPerson,
    signatureLocation: string,
    signatureFile: string,
) {
    // Get front page, with tax month and identification details
    const firstPage = doc.getPage(0);

    // Fillin name, national number and address
    firstPage.drawText(taxPerson.nationalRegisterNumber, { x: 305, y: 655, size: 10 })
    firstPage.drawText(taxPerson.fullName, { x: 305, y: 643, size: 10 })
    taxPerson.address.forEach((line, index) => {
        firstPage.drawText(line, { x: 305, y: 620 - index * 11, size: 10 })
    });

    // Get signature page
    const secondPage = doc.getPage(1);

    // Read signature picture and add it to the doc
    const signatureBytes = await readFile(signatureFile);
    const signatureImage = signatureFile.endsWith('.jpg')
        ? await doc.embedJpg(signatureBytes)
        : signatureFile.endsWith('.png')
            ? await doc.embedPng(signatureBytes)
            : undefined;
    const maxSize = { width: 200, height: 70 };

    // Add signature location and date
    secondPage.drawText(signatureLocation, { x: 85, y: 255, size: 10 })
    secondPage.drawText(new Date().toISOString().slice(0, 10), { x: 180, y: 255, size: 10 })

    // Draw the signature on the doc, make sure the picture is resized
    secondPage.drawImage(signatureImage, {
        x: 300,
        y: 235,
        width: (signatureImage.width / signatureImage.height < maxSize.width / maxSize.height) ? signatureImage.width * maxSize.height / signatureImage.height : maxSize.width,
        height: (signatureImage.width / signatureImage.height > maxSize.width / maxSize.height) ? signatureImage.height * maxSize.width / signatureImage.width : maxSize.height,
    });
}

/**
 * Draw a tax line as expected by the Belgian TST document.  The line should contain the number
 * of transactions, the tax basis and the tax amount.  The position should be the start of the line (left).
 * 
 * @param page The page to print the big number on.
 * @param transactionCount The number of transactions done.
 * @param taxBasis The amount of money to apply the tax on.
 * @param taxAmount The resulting tax to pay to the state.
 * @param position The position of the line.
 */
async function drawTaxLine(page: PDFPage, taxProduct: TaxProduct, position: { x: number, y: number }) {
    page.drawText(`${taxProduct.transactionCount}`, { x: position.x + 10, y: position.y, size: 15 });
    drawBigNumber(page, taxProduct.taxBasis, { x: position.x + 154, y: position.y }, 15);
    drawBigNumber(page, taxProduct.taxAmount, { x: position.x + 284, y: position.y }, 15);
}


/**
 * Read and parse a json payload at the given path on the filesystem.  If the provided
 * path is equal to '-', read from stdin instead.
 * 
 * @param path The path to load the json payload from
 * @returns The parsed json object
 */
function readJsonFile(path: string): any {
    return JSON.parse(readFileSync(path === '-' ? 0 : path, { encoding: 'utf-8' }))
}


async function main(
    formFile: string,
    signatureLocation: string,
    signatureFile: string,
    taxPerson: TaxPerson,
    taxData: TaxData,
    outputFile: string,
) {
    // Load empty tst file
    const formPdfBytes = await readFile(formFile);

    // Load a PDF with form fields
    const pdfDoc = await PDFDocument.load(formPdfBytes)

    const page = pdfDoc.getPage(0);

    // Add date
    page.drawText(`${taxData.month}`, { x: 275, y: 725, size: 10 })
    page.drawText(`${taxData.year % 100}`, { x: 288, y: 725, size: 10 })

    // Add tax info
    await Promise.all(taxData.products.map(product => drawTaxLine(page, product, taxProductsPositions[product.stockTax])))

    // Compute total amount and add it to the doc
    const total = taxData.products.reduce((acc, product) => acc + product.taxAmount, 0);
    drawBigNumber(page, total, { x: 508, y: 329 }, 15);

    // Final total
    const page2 = pdfDoc.getPage(1);
    drawBigNumber(page2, total, { x: 431, y: 372 }, 15)

    await fillInPersonalInfo(
        pdfDoc,
        taxPerson,
        signatureLocation,
        signatureFile,
    )

    // Serialize the PDFDocument to bytes (a Uint8Array)
    const pdfBytes = await pdfDoc.save()

    await writeFile(outputFile, pdfBytes);
}


// Setup up command, parse
program
    .description('Fill in the TST form for a given citizen and tax data')
    .requiredOption('--form-file <path>', 'Path to the TST form file (pdf) that we should fill in.', `${__dirname}/form-original.pdf`)
    .requiredOption('--signature-location <value>', 'The geographical location where the signature of the document is taking place', 'Bruxelles')
    .requiredOption('--signature-file <path>', 'Path to the image file that should be used as a signature.')
    .requiredOption('--tax-person <path>', 'Path to a file containing the data on the person filling in the form')
    .requiredOption('--tax-data <path>', 'Path to a file containing the data on the actual tax to pay to the state')
    .argument('<output-file>', 'The name of the filled in form file');

program.parse();

// Get all the options
const options = program.opts()
const outputFile = program.args[0];

main(
    options.formFile,
    options.signatureLocation,
    options.signatureFile,
    readJsonFile(options.taxPerson),
    readJsonFile(options.taxData),
    outputFile,
)
