from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp


class LoginForm(FlaskForm):
    email = StringField("이메일", validators=[DataRequired(), Email()])
    password = PasswordField("비밀번호", validators=[DataRequired()])
    remember = BooleanField("로그인 유지")


class SignupForm(FlaskForm):
    name = StringField("이름", validators=[DataRequired(), Length(min=2, max=60)])
    email = StringField("이메일", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField(
        "비밀번호",
        validators=[
            DataRequired(),
            Length(min=8, max=72, message="비밀번호는 8자 이상이어야 합니다."),
        ],
    )
    password_confirm = PasswordField(
        "비밀번호 확인",
        validators=[DataRequired(), EqualTo("password", message="비밀번호가 일치하지 않습니다.")],
    )
    phone = StringField(
        "휴대전화",
        validators=[
            DataRequired(),
            Regexp(r"^[0-9\-\s]{9,20}$", message="휴대전화 번호 형식이 올바르지 않습니다."),
        ],
    )
    agree_service = BooleanField("(필수) 서비스 이용약관", validators=[DataRequired()])
    agree_privacy = BooleanField("(필수) 개인정보 처리방침", validators=[DataRequired()])
    agree_marketing = BooleanField("(선택) 마케팅 정보 수신")
