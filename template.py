from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import io
import os


class FormTemplateGenerator:
    """Generates PDF templates with form fields for user data collection."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()

    def setup_custom_styles(self):
        """Setup custom paragraph styles for the form."""
        self.styles.add(
            ParagraphStyle(
                name="FormTitle",
                parent=self.styles["Heading1"],
                fontSize=18,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.darkblue,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="FieldLabel",
                parent=self.styles["Normal"],
                fontSize=12,
                spaceAfter=6,
                fontName="Helvetica-Bold",
                textColor=colors.black,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="FieldValue",
                parent=self.styles["Normal"],
                fontSize=11,
                spaceAfter=12,
                leftIndent=20,
                textColor=colors.black,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Heading2"],
                fontSize=14,
                spaceAfter=15,
                spaceBefore=20,
                textColor=colors.darkblue,
            )
        )

    def create_form_template(self) -> bytes:
        """
        Create a PDF template with all required form fields.

        Returns:
            bytes: PDF content as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Build the content
        story = []

        # Title
        title = Paragraph("Roommate Preference Form Template", self.styles["FormTitle"])
        story.append(title)
        story.append(Spacer(1, 20))

        # Instructions
        instructions = Paragraph(
            "Please fill out this form with your roommate preferences. "
            "You can download this template, convert it to .docx format, "
            "fill it out in Microsoft Word, and upload it back to the system.",
            self.styles["Normal"],
        )
        story.append(instructions)
        story.append(Spacer(1, 30))

        # Personal Information Section
        story.append(Paragraph("Personal Information", self.styles["SectionHeader"]))

        # Create form fields table
        form_data = [
            ["Field", "Your Response"],
            ["City", "_________________________________"],
            ["Area/Neighborhood", "_________________________________"],
            ["Budget (PKR)", "_________________________________"],
            ["Sleep Schedule", "_________________________________"],
            ["Cleanliness Level", "_________________________________"],
            ["Noise Tolerance", "_________________________________"],
            ["Study Habits", "_________________________________"],
            ["Food Preference", "_________________________________"],
            ["Additional Preferences", "_________________________________"],
            ["", "_________________________________"],
            ["", "_________________________________"],
            ["", "_________________________________"],
        ]

        # Create table
        table = Table(form_data, colWidths=[2.5 * inch, 3.5 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 11),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        story.append(table)
        story.append(Spacer(1, 30))

        # Field Descriptions
        story.append(Paragraph("Field Descriptions", self.styles["SectionHeader"]))

        descriptions = [
            ("City", "The city where you want to find accommodation"),
            ("Area/Neighborhood", "Specific area or neighborhood within the city"),
            ("Budget (PKR)", "Your monthly budget in Pakistani Rupees"),
            (
                "Sleep Schedule",
                "Your preferred sleep schedule (e.g., Early bird, Night owl, Flexible)",
            ),
            (
                "Cleanliness Level",
                "Your cleanliness standards (e.g., Very tidy, Tidy, Moderate, Relaxed)",
            ),
            (
                "Noise Tolerance",
                "Your tolerance for noise (e.g., Quiet preferred, Moderate noise ok, Loud ok)",
            ),
            (
                "Study Habits",
                "Your study patterns (e.g., Early morning, Late night, Flexible)",
            ),
            (
                "Food Preference",
                "Your dietary preferences (e.g., Vegetarian, Non-vegetarian, Vegan, Flexible)",
            ),
            (
                "Additional Preferences",
                "Any other specific requirements or preferences you have",
            ),
        ]

        for field, description in descriptions:
            story.append(
                Paragraph(f"<b>{field}:</b> {description}", self.styles["Normal"])
            )
            story.append(Spacer(1, 8))

        story.append(Spacer(1, 20))

        # Instructions for conversion
        story.append(Paragraph("Instructions", self.styles["SectionHeader"]))
        instructions_text = [
            "1. Download this PDF template",
            "2. Convert the PDF to .docx format using an online converter or software",
            "3. Open the .docx file in Microsoft Word",
            "4. Fill in all the required fields with your information",
            "5. Save the completed form",
            "6. Upload the filled .docx file back to the system",
        ]

        for instruction in instructions_text:
            story.append(Paragraph(instruction, self.styles["Normal"]))
            story.append(Spacer(1, 6))

        # Build PDF
        doc.build(story)

        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()

        return pdf_content

    def save_template_to_file(
        self, filename: str = "roommate_preference_template.pdf"
    ) -> str:
        """
        Save the template to a file and return the file path.

        Args:
            filename: Name of the file to save

        Returns:
            str: Path to the saved file
        """
        pdf_content = self.create_form_template()

        # Create templates directory if it doesn't exist
        templates_dir = "templates"
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)

        file_path = os.path.join(templates_dir, filename)

        with open(file_path, "wb") as f:
            f.write(pdf_content)

        return file_path


def generate_template() -> bytes:
    """
    Convenience function to generate a form template.

    Returns:
        bytes: PDF content as bytes
    """
    generator = FormTemplateGenerator()
    return generator.create_form_template()


def save_template_file(filename: str = "roommate_preference_template.pdf") -> str:
    """
    Convenience function to save template to file.

    Args:
        filename: Name of the file to save

    Returns:
        str: Path to the saved file
    """
    generator = FormTemplateGenerator()
    return generator.save_template_to_file(filename)


if __name__ == "__main__":
    # Test the template generation
    generator = FormTemplateGenerator()
    file_path = generator.save_template_to_file()
    print(f"Template saved to: {file_path}")