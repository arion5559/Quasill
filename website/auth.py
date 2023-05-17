import jsonify as jsonify
from flask import Blueprint, render_template, request, session, redirect, url_for
import re
from website.logic import get_user_by_id, login_user, register_user, update_user, delete_user, create_diagnostic, \
    read_all_diagnostics, read_diagnostic, proportionate_feedback, delete_diagnostic
from website.models import Diagnostic, new_diagnostic

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            if login_user(username, password):
                print("ha entrado")
                return render_template("index2.html", user=session.get('user_id'))
            else:
                print("no ha entrado")
                return redirect(url_for('auth.login'))
        except TypeError as e:
            print("Error:", e)
            return redirect(url_for('auth.login'))
    else:
        return render_template("login.html", user=session.get('user_id'))


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname1')
        surname2 = request.form.get('surname2')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        print(name, surname, surname2, username, email, password, password2)

        if password != password2:
            print("erro1")
            return redirect(url_for('auth.signup'))

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            print("error2")
            return redirect(url_for('auth.signup'))

        if not re.match(r"[A-Za-z0-9]+", username):
            print("error3")
            return redirect(url_for('auth.signup'))
        if not name or not surname or not username or not email or not password or not password2:
            print("error4")
            return redirect(url_for('auth.signup'))

        if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()])([a-zA-Z\d!@#$%^&*()]{8,})$", password):
            print("valida los datos")
            return redirect(url_for('auth.signup'))

        register_user(name, surname, username, email, password, surname2)
        print("usuario registrado")
        return redirect(url_for('auth.login'))
    else:
        return render_template("signup.html")
    print("jajaja error2")


@auth.route('/cuenta')
def cuenta():
    user = get_user_by_id(session['user_id'])
    return render_template("cuenta.html", user=user)


@auth.route('/editar', methods=['GET', 'POST'])
def editar():
    user_id = session.get('user_id')
    user = get_user_by_id(user_id)  # retrieve user information from the database
    if request.method == 'POST':
        if request.form['submit_button'] == 'btnUpdate':
            # update user information
            name = request.form.get('name')
            surname = request.form.get('surname1')
            surname2 = request.form.get('surname2')
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            update_user(user_id, name, surname, username, email, password, surname2)
            print("Usuario actualizado")
            return redirect(url_for('auth.cuenta'))
        elif request.form['submit_button'] == 'btnDelete':
            # delete user
            delete_user(user_id)
            print("Usuario eliminado")
            return redirect(url_for('views.index'))
    return render_template('editar.html', user=user)


@auth.route('/eliminar', methods=['GET', 'POST'])
def eliminar():
    if request.method == 'POST':
        return redirect(url_for('auth.eliminar_cuenta'))
    return render_template('eliminar.html')


@auth.route('/eliminar_cuenta', methods=['POST'])
def eliminar_cuenta():
    user_id = session.get('user_id')
    print(f"usuario: {user_id}")
    if user_id:
        if delete_user(user_id):
            session.clear()
            print('Usuario eliminado exitosamente', 'success')
        else:
            print('Usuario no encontrado', 'danger')
    else:
        print('Usuario no autenticado', 'danger')
    return redirect(url_for('views.index'))


@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('views.index'))


# RUTAS RELACIONADAS CON EL DIAGNÓSTICO

# RUTA QUE LLEVA A DIAGNOSTICO PARA QUE EL USUARIO PUEDA INTRODUCIR SUS SÍNTOMAS
@auth.route('/diagnostico', methods=['POST', 'GET'])
# no solo POST sino también GET por si alguien quiere acceder a la URL de /diagnostico de forma directa
def diagnostico():
    if request.method == 'POST':
        text = request.form.get('inputSintomas')
        print(text)
        user_id = session.get('user_id')
        print(user_id)
        diagnostic_data = create_diagnostic(user_id, text)
        print(diagnostic_data)
        return redirect(
            url_for('auth.resultados'))  # Redirigir a la página de resultados después de recibir los síntomas

    else:  # This is a GET request
        diagnostic_data = create_diagnostic(session.get('user_id'), '')
        return render_template('diagnostico.html', diagnostic=diagnostic_data)


# RUTA QUE MUESTRA LOS RESULTADOS DEL DIAGNÓSTICO
@auth.route('/resultados', methods=['GET'])
def resultados():
    # Puedes pasar un texto vacío o el último texto ingresado en el diagnóstico
    diagnostic_data = create_diagnostic(session.get('user_id'), '')
    return render_template('resultados.html', diagnostic=diagnostic_data)


@auth.route('/diagnostics', methods=['GET'])
def read_all_diagnostics_route():
    user_id = session.get('user_id')
    diagnostics = read_all_diagnostics(user_id)
    return jsonify(diagnostics), 200


@auth.route('/diagnostic/<int:diagnostic_id>', methods=['GET'])
def get_diagnostic(user_id: str, diagnostic_index: int) -> Diagnostic:
    diagnostic = read_diagnostic(user_id, diagnostic_index)
    return jsonify(diagnostic), 200


@auth.route('/diagnostics/<int:diagnostic_id>', methods=['PUT'])
def update_diagnostic_route(diagnostic_id):
    user_id = session.get('user_id')
    correct_label = request.json.get('correct_label')
    success = proportionate_feedback(user_id, diagnostic_id, correct_label)
    if success:
        return jsonify({'status': 'success', 'message': 'Diagnostic updated'}), 200
    else:
        return jsonify({'status': 'failure', 'message': 'Diagnostic not found'}), 404


@auth.route('/diagnostics/<int:diagnostic_id>', methods=['DELETE'])
def delete_diagnostic_route(diagnostic_id):
    user_id = session.get('user_id')
    success = delete_diagnostic(user_id, diagnostic_id)
    if success:
        return jsonify({'status': 'success', 'message': 'Diagnostic deleted'}), 200
    else:
        return jsonify({'status': 'failure', 'message': 'Diagnostic not found'}), 404


@auth.route('/feedback.html', methods=['GET'])
def feedback_html():
    return render_template('feedback.html')