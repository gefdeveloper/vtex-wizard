import re, random, requests, os
import pandas as pd
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from urllib.parse import urlparse
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords


def generate_random_numbers(random_numbers_quantity: int):
    """Generates a list of random EAN codes of 13 digits."""
    numbers = []
    for _ in range(random_numbers_quantity):
        # Generar el primer dígito aleatorio, asegurándonos de que no sea cero
        first_digit = str(random.randint(1, 9))
        # Generar los restantes 12 dígitos aleatorios
        remaining_digits = "".join([str(random.randint(0, 9)) for _ in range(12)])
        # Combinar los dígitos para formar el número completo
        number = first_digit + remaining_digits
        numbers.append(number)
    return numbers


def save_to_excel(numbers_list: list):
    """Saves a list of EAN codes to an Excel file."""
    df = pd.DataFrame({"EAN": numbers_list})
    df.to_excel("./excel-files/ean/ean_codes.xlsx", index=False)


def escape_string(input_string: str):
    """Replaces characters '-' with '\-', and characters '.' with '\.'"""
    return re.sub(r"[-.]", lambda x: "\\" + x.group(), input_string)


def html_to_text(html):
    """Convert a snippet of HTML into plain text."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text()


def change_html_to_text():
    """Read an Excel file containing HTML in a specified column, convert that HTML into plain text
    using the html_to_text function, and save the result to a new Excel file."""

    df = pd.read_excel("./excel-files/descriptions/description-html.xlsx")

    # Aplicar la función html_to_text a cada valor de la columna 'columna_html'
    df["columna_texto"] = df["columna_html"].apply(html_to_text)

    # Guardar el DataFrame resultante en un nuevo archivo Excel
    df.to_excel("./excel-files/descriptions/description-text.xlsx", index=False)


def procesar_imagen(url, sku, carpeta_destino):
    """Function to download and process an image."""
    enlaces_separados = url.split("|")

    for i, enlace in enumerate(enlaces_separados, start=1):
        nombre_archivo = f"{sku}-{i}.jpg"  # Nombre del archivo será SKU-i.jpg
        ruta_archivo = os.path.join(
            carpeta_destino, nombre_archivo
        )  # Ruta completa del archivo
        parsed_url = urlparse(enlace)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, como Gecko) Chrome/58.0.3029.110 Safari/537.3",
                "Referer": base_url,
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Accept": "image/webp,image/apng,image/,/*;q=0.8",
            }
            respuesta = requests.get(
                enlace.strip(), headers=headers
            )  # Eliminar espacios en blanco
            if respuesta.ok:
                imagen = Image.open(BytesIO(respuesta.content))
                # Verificar si la imagen ya tiene las dimensiones y el formato requeridos
                if imagen.size == (1000, 1000) and imagen.format == "JPEG":
                    print(
                        f"La imagen {enlace} ya está en las dimensiones y formato requeridos. Descargando sin modificar."
                    )
                    with open(ruta_archivo, "wb") as f:
                        f.write(respuesta.content)
                    continue  # Pasar a la próxima iteración sin procesar la imagen

                imagen = imagen.convert("RGB")  # Convertir la imagen a formato RGB

                # Redimensionar la imagen manteniendo su relación de aspecto original
                max_dimension = 1000
                ancho, alto = imagen.size
                proporcion = max_dimension / max(ancho, alto)
                nuevo_ancho = round(ancho * proporcion)
                nuevo_alto = round(alto * proporcion)
                imagen = imagen.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)

                # Crear un lienzo blanco de 1000x1000 píxeles y pegar la imagen en el centro
                lienzo = Image.new("RGB", (max_dimension, max_dimension), color="white")
                posicion_x = (max_dimension - nuevo_ancho) // 2
                posicion_y = (max_dimension - nuevo_alto) // 2
                lienzo.paste(imagen, (posicion_x, posicion_y))

                lienzo.save(
                    ruta_archivo, "JPEG", quality=95
                )  # Guardar la imagen en formato JPEG
                print(f"Imagen guardada: {ruta_archivo}")
            else:
                print(f"Error al descargar la imagen {enlace}: {respuesta.status_code}")
        except Exception as e:
            print(f"Error al procesar la imagen {enlace}: {e}")


def save_images_from_excel(archivo_excel, carpeta_destino):
    """Extracts image URLs from an Excel file and saves the corresponding images to the specified destination folder."""
    df = pd.read_excel(archivo_excel)
    for index, fila in df.iterrows():
        enlaces_imagen = fila["url"]
        sku = fila["SKU"]
        if (
            not pd.isna(enlaces_imagen)
            and not pd.isnull(enlaces_imagen)
        ):
            procesar_imagen(enlaces_imagen, sku, carpeta_destino)



def check_excel_path(ruta):
    """Verifies if the provided path has the correct format."""
    if not ruta:
        return False

    if not os.path.isabs(ruta):
        return False

    if not os.path.exists(ruta):
        os.makedirs(ruta)

    return True


def check_url(url):
    """Verifies if the URL has the correct format and if it is accessible."""

    parsed_url = urlparse(url)
    if not all([parsed_url.scheme, parsed_url.netloc]):
        return True

    try:
        response = requests.head(url)
        if response.ok:
            return True
        elif response.status_code == 403:
            return 403
        elif response.status_code == 404:
            return 404
    except requests.ConnectionError:
        return False


def create_excel_non_working_urls(archivo_excel, carpeta_destino):
    """Reads an Excel file containing URLs, checks if they are valid and accessible, and saves the non-working URLs to a new Excel file."""
    try:

        df = pd.read_excel(archivo_excel)

        urls_no_funcionan = []

        for index, fila in df.iterrows():

            # Verificar si el valor en la columna "url" es una cadena antes de intentar dividirla
            enlaces_imagen = fila["url"]
            sku = fila["SKU"]
            # Verificar si el SKU contiene el carácter "/"
            if "/" in sku:
                urls_no_funcionan.append(
                    {
                        "SKU": sku,
                        "URL": enlaces_imagen,
                        "Comentario": "El SKU tiene el carácter /",
                    }
                )
                print(f"El SKU {sku} tiene el carácter /")
                continue
            if pd.notnull(enlaces_imagen) and isinstance(enlaces_imagen, str):
                # Dividir los enlaces por los separadores "|"
                urls = enlaces_imagen.split("|")
                for url in urls:
                    if check_url(url) == False:
                        urls_no_funcionan.append(
                            {
                                "SKU": sku,
                                "URL": url,
                                "Comentario": "URL no válida",
                            }
                        )
                        print(f"URL no funciona para SKU {sku}: {url}")
                    elif check_url(url) == 403:
                        urls_no_funcionan.append(
                            {
                                "SKU": sku,
                                "URL": url,
                                "Comentario": "La URL no existe o no se puede descargar con este programa sino de forma manual.",
                            }
                        )
                    elif check_url(url) == 404:
                        urls_no_funcionan.append(
                            {
                                "SKU": sku,
                                "URL": url,
                                "Comentario": "La URL no existe",
                            }
                        )
                    elif url == "":
                        urls_no_funcionan.append(
                            {
                                "SKU": sku,
                                "URL": url,
                                "Comentario": "Celda vacía",
                            }
                        )
            else:
                sku = fila["SKU"]
                urls_no_funcionan.append(
                    {
                        "SKU": sku,
                        "URL": enlaces_imagen,
                        "Comentario": "URL no especificada o no es una cadena válida",
                    }
                )
                print(
                    f"URL no especificada o no es una cadena válida para SKU {sku}: {enlaces_imagen}"
                )

        df_urls_no_funcionan = pd.DataFrame(urls_no_funcionan)

        archivo_resultado = os.path.join(carpeta_destino, "failed_urls.xlsx")
        df_urls_no_funcionan.to_excel(archivo_resultado, index=False)
        print(f"Se han guardado las URL que no funcionan en '{archivo_resultado}'.")
        return len(urls_no_funcionan)

    except Exception as e:
        print(f"Error al procesar el archivo Excel: {e}")


def format_image_excel_file():
    """Reads an Excel file with SKU and URL columns, groups the URLs by SKU, and saves the result to a new Excel file."""
    df = pd.read_excel("./excel-files/format/raw-excel-file.xlsx")

    df_grouped = df.groupby("SKU")["url"].apply(lambda x: "|".join(x)).reset_index()

    df_grouped.to_excel("./excel-files/format/formatted-excel-file.xlsx", index=False)


def create_keywords_of_product_name(texto):
    # Tokenizar el texto en palabras
    palabras = word_tokenize(texto)

    # Eliminar palabras vacías (palabras comunes como "el", "es", "y", etc.)
    palabras_vacias = set(stopwords.words("spanish"))
    palabras = [
        palabra.lower()
        for palabra in palabras
        if palabra.lower() not in palabras_vacias
    ]

    # Eliminar caracteres especiales usando expresiones regulares
    palabras = [re.sub(r"[^a-zA-Z0-9áéíóúü]", "", palabra) for palabra in palabras]

    # Eliminar cadenas vacías después de eliminar los caracteres especiales
    palabras = [palabra for palabra in palabras if palabra]

    # Contar la frecuencia de cada palabra
    frecuencia_palabras = {}
    for palabra in palabras:
        frecuencia_palabras[palabra] = frecuencia_palabras.get(palabra, 0) + 1

    # Ordenar las palabras por frecuencia en orden descendente
    palabras_ordenadas = sorted(
        frecuencia_palabras.items(), key=lambda x: x[1], reverse=True
    )

    # Devolver las 10 palabras clave principales (puedes ajustar este número según sea necesario)
    return [palabra for palabra, _ in palabras_ordenadas[:20]]


def create_keywords(texto, categoria):
    if isinstance(texto, str):  # Verifica si el texto es una cadena de caracteres
        texto = texto.replace("/", " ")
        # Generar palabras clave utilizando la función generate_keywords
        keywords = create_keywords_of_product_name(texto)
        # Filtrar sustantivos y excluir palabras no deseadas
        sustantivos = [
            palabra
            for palabra in keywords
            if palabra
            not in [
                "ml",
                "–",
                "gr",
                "u",
                "kg",
                "pcs",
                "piezas",
                "pieza",
                "cm",
                "mm",
                "w",
                "l",
                "m",
                "unidad",
                "unidades",
                "und",
                "unds",
                "un",
                "pa",
            ]
        ]
        # Agregar la categoría como palabra clave
        categoria_keywords = [categoria.lower()]
        sustantivos.extend(categoria_keywords)
        return ", ".join(sustantivos)
    else:
        return ""


def generate_keywords_excel_file():
    # Descarga los recursos necesarios de NLTK
    nltk.download("punkt")
    nltk.download("averaged_perceptron_tagger")
    nltk.download("stopwords")

    # Carga el archivo Excel
    df = pd.read_excel("./excel-files/keywords/products-list.xlsx")

    # Selecciona las columnas de interés
    columna_nombre = "Nombre"
    columna_categoria = "Categoria"

    # Aplica la función a las columnas seleccionadas
    df["keywords"] = df.apply(
        lambda row: create_keywords(row[columna_nombre], row[columna_categoria]),
        axis=1,
    )
    # Guarda el resultado en un nuevo archivo Excel
    df.to_excel("./excel-files/keywords/keywords-list.xlsx", index=False)


def crop_margins(
    imagen_path, margen_inferior, margen_superior, margen_izquierda, margen_derecha
):
    # Abrir la imagen
    imagen = Image.open(imagen_path)

    # Obtener dimensiones de la imagen
    ancho, alto = imagen.size

    # Definir el área a recortar (left, upper, right, lower)
    izquierda = margen_izquierda
    superior = margen_superior
    derecha = ancho - margen_derecha
    inferior = alto - margen_inferior

    # Recortar la imagen
    imagen_recortada = imagen.crop((izquierda, superior, derecha, inferior))

    return imagen_recortada


def save_cropped_image(
    margen_inferior, margen_superior, margen_izquierda, margen_derecha
):
    # Recortar la imagen
    imagen_recortada = crop_margins(
        "./media/images/image-to-crop.jpg",
        margen_inferior,
        margen_superior,
        margen_izquierda,
        margen_derecha,
    )

    # Guardar la imagen recortada
    imagen_recortada.save("./media/images/cropped-image.jpg")


def verificar_columnas_excel_de_imagenes(ruta_archivo):
    try:
        # Leer el archivo Excel
        df = pd.read_excel(ruta_archivo)

        # Verificar si las columnas 'SKU' y 'url' están en el DataFrame
        if "SKU" in df.columns and "url" in df.columns:
            return True
        else:
            return None
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None


def verificar_columnas_excel_de_descripciones(ruta_archivo):
    try:
        # Leer el archivo Excel
        df = pd.read_excel(ruta_archivo)

        # Verificar si las columnas 'SKU' y 'url' están en el DataFrame
        if "columna_html" in df.columns:
            return True
        else:
            return None
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None


def verificar_columnas_excel_de_keywords(ruta_archivo):
    try:
        # Leer el archivo Excel
        df = pd.read_excel(ruta_archivo)

        # Verificar si las columnas 'SKU' y 'url' están en el DataFrame
        if "Nombre" in df.columns and "Categoria" in df.columns:
            return True
        else:
            return None
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None


def verificar_columnas_excel_de_imagenes_sin_formato(ruta_archivo):
    try:
        # Leer el archivo Excel
        df = pd.read_excel(ruta_archivo)

        # Verificar si las columnas 'SKU' y 'url' están en el DataFrame
        if "Nombre" in df.columns and "Categoria" in df.columns:
            return True
        else:
            return None
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None
