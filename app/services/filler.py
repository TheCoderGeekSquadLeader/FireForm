from datetime import datetime

from pdfrw import PdfReader, PdfWriter, PdfName

from app.services.llm import LLM


class Filler:
    def __init__(self):
        pass

    def fill_form(self, pdf_form: str, llm: LLM):
        """
        Fill a PDF form with values from user_input using LLM.
        Fields are filled in the visual order (top-to-bottom, left-to-right).
        """
        output_pdf = (
            pdf_form[:-4]
            + "_"
            + datetime.now().strftime("%Y%m%d_%H%M%S")
            + "_filled.pdf"
        )

        # Generate dictionary of answers from your original function
        t2j = llm.main_loop()
        textbox_answers = t2j.get_data()  # This is a dictionary

        answers_list = list(textbox_answers.values())

        # Read PDF
        pdf = PdfReader(pdf_form)

        # Loop through pages
        i = 0
        for page in pdf.pages:
            if page.Annots:
                sorted_annots = sorted(
                    page.Annots, key=lambda a: (-float(a.Rect[1]), float(a.Rect[0]))
                )

                for annot in sorted_annots:
                    if annot.Subtype == "/Widget" and annot.T:
                        if i < len(answers_list):
                            val = answers_list[i]
                            
                            # Inspection du type de champ pour identifier les boutons / cases à cocher (/Btn)
                            ft = getattr(annot, 'FT', None)
                            if ft == '/Btn':
                                # Traduction de la réponse de l'IA en état booléen
                                is_checked = False
                                if isinstance(val, bool):
                                    is_checked = val
                                elif isinstance(val, str):
                                    is_checked = val.lower() in ['true', 'yes', '1', 'on', 'checked', 'oui']
                                
                                # Attribution de la valeur et de l'état d'affichage (Appearance State)
                                if is_checked:
                                    annot.V = PdfName('/Yes')
                                    annot.AS = PdfName('/Yes')
                                else:
                                    annot.V = PdfName('/Off')
                                    annot.AS = PdfName('/Off')
                                annot.AP = None
                            else:
                                # Logique standard pour les champs de texte (/Tx)
                                annot.V = f"{val}"
                                annot.AP = None
                                
                            i += 1
                        else:
                            # Stop if we run out of answers
                            break

        PdfWriter().write(output_pdf, pdf)

        # Your main.py expects this function to return the path
        return output_pdf