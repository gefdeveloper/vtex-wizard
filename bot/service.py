import re, random, requests, os, ollama, logging
import pandas as pd
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from urllib.parse import urlparse
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from openai import OpenAI
import pandas as pd


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


def parse_html(element, text_parts):
    """
    Processes an HTML element and formats its content into plain text.
    
    Args:
        element (Tag): A BeautifulSoup element representing an HTML tag.
        text_parts (list): List that accumulates the processed text parts.
    """
    # Manejo de listas desordenadas <ul> y <li>
    if element.name == "ul":  # Si es una lista desordenada
        for li in element.find_all(
            "li", recursive=False
        ):  # Recorre solo los <li> hijos directos
            text_parts.append(
                f"• {li.get_text(strip=True)}\n"
            )  # Añadir viñeta y el texto del <li>

    # Manejo de listas ordenadas <ol> y <li>
    elif element.name == "ol":  # Si es una lista ordenada
        for idx, li in enumerate(
            element.find_all("li", recursive=False), 1
        ):  # Enumerar los <li>
            text_parts.append(
                f"{idx}. {li.get_text(strip=True)}\n"
            )  # Añadir el número y el texto del <li>

    # Manejo de títulos <h1>, <h2>, etc.
    elif element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        text_parts.append(
            f"\n{element.get_text(strip=True).upper()}\n"
        )  # Títulos en mayúsculas

    # Manejo de párrafos <p>
    elif element.name == "p":
        text_parts.append(
            f"{element.get_text(strip=True)}\n\n"
        )  # Añadir el texto del párrafo con doble salto de línea

    # Manejo de texto en negrita <strong> o <b>
    elif element.name in ["strong", "b"]:
        text_parts.append(
            f"**{element.get_text(strip=True)}**"
        )  # Añadir negritas con **

    # Manejo de <span> para extraer el texto
    elif element.name == "span":
        text_parts.append(
            f"{element.get_text(strip=True)}"
        )  # Extraer el texto del <span> sin formato especial

    # Manejo de otros elementos que contengan texto
    elif element.string and element.name not in ["ul", "ol", "li"]:
        text_parts.append(
            element.string.strip()
        )  # Añadir solo el contenido de texto, si no es lista

    # Procesar etiquetas anidadas (pero solo si no es una etiqueta de texto)
    if element.name and element.name not in [
        "ul",
        "ol",
        "li",
    ]:  # Evita duplicar <li> y <ul>/<ol>
        for child in element.children:
            parse_html(child, text_parts)


def html_to_text(html):
    """
    Convert an HTML fragment into plain text, even when closing tags are missing.

    Args:
        html (str): An HTML fragment to be converted into plain text.

    Returns:
        str: The content of the HTML converted to plain text.
    """
    soup = BeautifulSoup(
        html, "html.parser"
    )  # El parser 'html.parser' manejará el HTML mal formado

    text_parts = []  # Lista para acumular las partes del texto

    # Iniciar el procesamiento del HTML desde el nivel más alto
    root_element = (
        soup.body if soup.body else soup
    )  # Si no hay body, recorrer desde el nivel superior
    for elem in root_element.children:
        parse_html(elem, text_parts)

    # Combinar las partes del texto y devolver el resultado
    return "".join(text_parts).replace("_x000D_", "").strip()


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


def obtener_tamano_carpeta(carpeta):
    """Devuelve el tamaño total en bytes de todos los archivos dentro de una carpeta."""
    tamano_total = 0
    for ruta_directorio, _, archivos in os.walk(carpeta):
        for archivo in archivos:
            ruta_archivo = os.path.join(ruta_directorio, archivo)
            tamano_total += os.path.getsize(ruta_archivo)
    return tamano_total


def save_images_from_excel(archivo_excel, carpeta_base_destino):
    """Extrae las URL de imágenes de un archivo Excel y guarda las imágenes en carpetas según el peso."""

    TAMANO_MAXIMO_CARPETA = 50 * 1024 * 1024  # 20 MB
    df = pd.read_excel(archivo_excel)
    numero_carpeta = 1
    carpeta_destino = os.path.join(carpeta_base_destino, f"Lote_{numero_carpeta}")
    os.makedirs(carpeta_destino, exist_ok=True)

    for index, fila in df.iterrows():
        enlaces_imagen = fila["url"]
        sku = fila["SKU"]

        if not pd.isna(enlaces_imagen) and not pd.isnull(enlaces_imagen):
            # Procesar la imagen y guardarla en la carpeta actual
            procesar_imagen(enlaces_imagen, sku, carpeta_destino)

            # Verificar si el tamaño de la carpeta supera el límite
            tamano_actual_carpeta = obtener_tamano_carpeta(carpeta_destino)
            if tamano_actual_carpeta >= TAMANO_MAXIMO_CARPETA:
                # Crear una nueva carpeta si se supera el tamaño máximo
                numero_carpeta += 1
                carpeta_destino = os.path.join(
                    carpeta_base_destino, f"Lote_{numero_carpeta}"
                )
                os.makedirs(carpeta_destino, exist_ok=True)


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
        elif response.status_code == 503:
            return 503
    except requests.ConnectionError:
        return False


def create_excel_non_working_urls(archivo_excel, carpeta_destino):
    """Reads an Excel file containing URLs, checks if they are valid and accessible, and saves the non-working URLs to a new Excel file."""
    try:

        df = pd.read_excel(archivo_excel)
        urls_no_funcionan = []

        for index, fila in df.iterrows():
            enlaces_imagen = fila["url"]
            sku = str(fila["SKU"])

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
                # Dividir los enlaces por el separador "|" o procesar el único enlace si no hay "|"
                urls = (
                    enlaces_imagen.split("|")
                    if "|" in enlaces_imagen
                    else [enlaces_imagen]
                )

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
                    elif check_url(url) == 503:
                        urls_no_funcionan.append(
                            {
                                "SKU": sku,
                                "URL": url,
                                "Comentario": "El servidor no está disponible temporalmente (Error 503).",
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
        return None


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


def generate_keywords_excel_file_2():
    # Cargar el archivo Excel con la lista de productos
    file_path = "./excel-files/keywords/products-list.xlsx"  # Cambia esto a la ruta de tu archivo Excel
    df = pd.read_excel(file_path)
    # Iterables
    products_list = df["Nombre"].astype(str).tolist()
    brands_list = df["Marca"].astype(str).tolist()
    categories_list = df["Categoria"].astype(str).tolist()
    # Inicializar una lista para almacenar las keywords generadas
    keywords_list = []

    # Iterar sobre cada producto y generar las keywords
    for product, brand, category in zip(products_list, brands_list, categories_list):
        # Crear el mensaje para el modelo
        # prompt = f"Enviame solo una lista de keywords comerciales separadas por coma para el siguiente producto: {product} de la marca {brand} y categoría en {category}"
        prompt = (
            f"Genera una lista concisa de keywords comerciales, separadas por comas, "
            f"para un producto como '{product}', de la marca '{brand}', "
            f"en la categoría '{category}'."
        )
        # Llamar al modelo de Ollama
        response = ollama.chat(
            model="llama3.1:latest",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        # Extraer las keywords generadas
        content = response["message"]["content"]

        # Usar regex para extraer solo la lista de keywords
        keywords_match = re.search(r"([\w\s]+,)+[\w\s]+", content)
        keywords = keywords_match.group(0) if keywords_match else content

        # Eliminar los renglones en blanco antes y después de las keywords
        keywords = keywords.strip()

        # Agregar las keywords a la lista
        keywords_list.append(keywords)

    df = pd.DataFrame({"Nombre": products_list, "Keywords": keywords_list})

    # Guardar el DataFrame en un archivo Excel
    df.to_excel("./excel-files/keywords/keywords-list.xlsx", index=False)


def generation_description_exce_file():
    # Cargar el archivo Excel con la lista de productos
    file_path = "./excel-files/descriptions/products-list.xlsx"  # Cambia esto a la ruta de tu archivo Excel
    df = pd.read_excel(file_path)

    # Inicializar una lista para almacenar las descripciones generadas
    descriptions_list = []
    products_list = df["Nombre"].astype(str).tolist()
    # Iterar sobre cada producto y generar las descripciones
    for product in products_list:
        # Crear el mensaje para el modelo
        prompt = f"Genera una descripción comercial atractiva para el siguiente producto en un párrafo de máximo 500 caracteres: {product}"

        # Llamar al modelo de Ollama
        response = ollama.chat(
            model="llama3.1:latest",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        # Extraer la descripción generada
        description = response["message"]["content"]

        # Eliminar los renglones en blanco antes y después de la descripción
        description = description.strip()

        # Agregar la descripción a la lista
        descriptions_list.append(description)

    # Agregar las descripciones generadas como una nueva columna en el DataFrame
    df = pd.DataFrame(
        {"Nombre": products_list, "Descripción Comercial": descriptions_list}
    )

    df.to_excel("./excel-files/descriptions/descriptions-list.xlsx", index=False)


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


def verificar_columnas_excel_de_generacion_descripciones(ruta_archivo):
    try:
        # Leer el archivo Excel
        df = pd.read_excel(ruta_archivo)

        # Verificar si las columnas 'SKU' y 'url' están en el DataFrame
        if "Nombre" in df.columns:
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
        if (
            "Nombre" in df.columns
            and "Marca" in df.columns
            and "Categoria" in df.columns
        ):
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


def escape_string(input_string):
    """Replaces characters '-' with '\-', and characters '.' with '\.'"""
    return re.sub(r"[-.\\]", lambda x: "\\" + x.group(), input_string)


def generar_keywords(nombre, categoria, marca):
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = (
        f"Genera keywords relevantes para un producto con estas características:\n"
        f"Nombre: {nombre}\n"
        f"Categoría: {categoria}\n"
        f"Marca: {marca}\n"
        "Proporciona una lista de keywords separadas por comas."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": f"{prompt}"}]
        )

        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Error en la API de OpenAI: {str(e)}")
        return "Ocurrió un error al generar las keywords"


def generar_excel_de_keywords():
    # Leer el archivo Excel con las columnas 'Nombre', 'Categoria', y 'Marca'
    df = pd.read_excel("./excel-files/keywords/products-list.xlsx")

    # Crear una lista vacía para almacenar las keywords
    keywords_list = []

    # Iterar sobre cada fila y generar keywords
    for index, row in df.iterrows():
        nombre = row["Nombre"]
        categoria = row["Categoria"]
        marca = row["Marca"]

        try:
            keywords = generar_keywords(nombre, categoria, marca)
            keywords_list.append(keywords)
            print(f"Se generó los keywords para {nombre}")
        except Exception as e:
            print(f"Error al generar las keywords para {nombre}: {e}")
            keywords_list.append("Keywords no disponibles")

    # Añadir las keywords al DataFrame
    df["Keywords"] = keywords_list

    # Guardar el DataFrame actualizado en un nuevo archivo Excel
    df.to_excel("./excel-files/keywords/keywords-list.xlsx", index=False)


def generar_descripcion(producto):
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"Genera una descripción comercial en un párrafo de máximo 500 caracteres para este producto: {producto}"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", messages=[{"role": "user", "content": f"{prompt}"}]
        )

        return response.choices[0].message.content
    except Exception as e:
        logging(f"Error en la API de OpenAI: {str(e)}")
        return "Ocurrió un error al generar la descripción"


def generar_excel_de_descripciones():
    # Leer el archivo Excel con la columna "Productos"
    df = pd.read_excel("./excel-files/descriptions/products-list.xlsx")

    # Crear una lista vacía para almacenar las descripciones
    descripciones = []

    # Iterar sobre la columna 'Productos' y generar descripciones
    for producto in df['Nombre']:
        try:
            descripcion = generar_descripcion(producto)
            descripciones.append(descripcion)
            print(f"Se generó la descripción para {producto}")
        except Exception as e:
            print(f"Error al generar la descripción para {producto}: {e}")
            descripciones.append("Descripción no disponible")

    # Añadir las descripciones al DataFrame
    df['Descripción'] = descripciones

    # Guardar el DataFrame actualizado en un nuevo archivo Excel
    df.to_excel("./excel-files/descriptions/descriptions-list.xlsx", index=False)

