import smtplib
import os
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.application import MIMEApplication
from config import config
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.host = config.EMAIL_HOST
        self.port = config.EMAIL_PORT
        self.use_tls = config.EMAIL_USE_TLS
        self.timeout = config.EMAIL_TIMEOUT
        
        # Estas credenciales deberían estar en variables de entorno en producción
        self.username = os.getenv('ALPAPEL_EMAIL', 'cartera@alpapel.com')
        self.password = os.getenv('ALPAPEL_EMAIL_PASSWORD', '')
        
        self.is_configured = bool(self.username and self.password)
    
    def enviar_email(self, destinatario, asunto, cuerpo_html, cuerpo_texto="", archivo_adjunto=None):
        """Envía un email usando SMTP"""
        if not self.is_configured:
            logger.warning("Servicio de email no configurado. Credenciales faltantes.")
            return False
            
        try:
            # Crear mensaje
            mensaje = MimeMultipart('alternative')
            mensaje['Subject'] = asunto
            mensaje['From'] = f"Sistema CRM Alpapel <{self.username}>"
            mensaje['To'] = destinatario
            
            # Agregar partes del mensaje
            parte_texto = MimeText(cuerpo_texto, 'plain', 'utf-8')
            parte_html = MimeText(cuerpo_html, 'html', 'utf-8')
            
            mensaje.attach(parte_texto)
            mensaje.attach(parte_html)
            
            # Agregar archivo adjunto si existe
            if archivo_adjunto and os.path.exists(archivo_adjunto):
                with open(archivo_adjunto, "rb") as archivo:
                    adjunto = MIMEApplication(archivo.read(), _subtype="pdf")
                    adjunto.add_header(
                        'Content-Disposition', 
                        'attachment', 
                        filename=os.path.basename(archivo_adjunto)
                    )
                    mensaje.attach(adjunto)
            
            # Enviar email
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout) as server:
                if self.use_tls:
                    server.starttls()
                
                server.login(self.username, self.password)
                server.send_message(mensaje)
            
            logger.info(f"Email enviado exitosamente a: {destinatario}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Error de autenticación SMTP: {str(e)}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"Error SMTP enviando email a {destinatario}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error enviando email a {destinatario}: {str(e)}")
            return False
    
    def enviar_bienvenida(self, destinatario, nombre_usuario, password_temporal):
        """Envía email de bienvenida con credenciales temporales"""
        asunto = "🎉 Bienvenido al Sistema CRM - ALPAPEL SAS"
        
        cuerpo_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #00B3B0, #009690); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; background: #f9f9f9; }}
                .credentials {{ background: #e8f4f8; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #00B3B0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; padding: 20px; background: #f0f0f0; }}
                .warning {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #ffc107; }}
                .code {{ font-family: 'Courier New', monospace; font-size: 18px; font-weight: bold; background: #2d3748; color: #ffffff; padding: 10px; border-radius: 5px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Bienvenido a CRM Alpapel</h1>
                    <p>Sistema de Gestión de Cartera</p>
                </div>
                <div class="content">
                    <p>Hola <strong>{nombre_usuario}</strong>,</p>
                    <p>Tu cuenta ha sido creada exitosamente en el Sistema de Gestión de Cartera de <strong>ALPAPEL SAS</strong>.</p>
                    
                    <div class="credentials">
                        <h3 style="color: #00B3B0; margin-top: 0;">🔐 Tus Credenciales de Acceso:</h3>
                        <p><strong>Usuario:</strong> {destinatario}</p>
                        <p><strong>Contraseña Temporal:</strong> <span class="code">{password_temporal}</span></p>
                    </div>
                    
                    <div class="warning">
                        <p><strong>⚠️ Importante:</strong></p>
                        <ul>
                            <li>Cambia tu contraseña en tu primer acceso</li>
                            <li>Esta contraseña es temporal y expira en 24 horas</li>
                            <li>Usa siempre tu email corporativo @alpapel.com</li>
                            <li>No compartas tus credenciales con nadie</li>
                        </ul>
                    </div>
                    
                    <p>Puedes acceder al sistema desde la aplicación CRM de cartera.</p>
                    
                    <p style="margin-top: 30px;">
                        Saludos cordiales,<br>
                        <strong>Equipo de Sistemas - ALPAPEL SAS</strong>
                    </p>
                </div>
                <div class="footer">
                    <p>Este es un mensaje automático, por favor no respondas a este email.</p>
                    <p>ALPAPEL SAS - Sistema CRM de Cartera</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        cuerpo_texto = f"""
        Bienvenido al Sistema CRM - ALPAPEL SAS
        
        Hola {nombre_usuario},
        
        Tu cuenta ha sido creada exitosamente en el Sistema de Gestión de Cartera.
        
        Credenciales de acceso:
        Usuario: {destinatario}
        Contraseña Temporal: {password_temporal}
        
        Importante:
        - Cambia tu contraseña en tu primer acceso
        - Esta contraseña es temporal y expira en 24 horas
        - Usa siempre tu email corporativo @alpapel.com
        - No compartas tus credenciales con nadie
        
        Puedes acceder al sistema desde la aplicación CRM de cartera.
        
        Saludos cordiales,
        Equipo de Sistemas - ALPAPEL SAS
        
        ---
        Este es un mensaje automático, por favor no respondas a este email.
        """
        
        return self.enviar_email(destinatario, asunto, cuerpo_html, cuerpo_texto)
    
    def enviar_recuperacion_password(self, destinatario, nombre_usuario, reset_token):
        """Envía email para recuperación de contraseña"""
        asunto = "🔒 Restablecer Contraseña - CRM ALPAPEL SAS"
        
        cuerpo_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #F57C00, #E57100); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; background: #f9f9f9; }}
                .token {{ background: #fff3cd; padding: 25px; border-radius: 8px; margin: 20px 0; text-align: center; border: 2px dashed #f59e0b; }}
                .code {{ font-family: 'Courier New', monospace; font-size: 24px; font-weight: bold; letter-spacing: 3px; color: #92400e; background: #fef3c7; padding: 15px; border-radius: 5px; display: inline-block; }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; padding: 20px; background: #f0f0f0; }}
                .warning {{ background: #fee2e2; padding: 15px; border-radius: 5px; margin: 15px 0; border-left: 4px solid #dc2626; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔒 Restablecer Contraseña</h1>
                </div>
                <div class="content">
                    <p>Hola <strong>{nombre_usuario}</strong>,</p>
                    <p>Has solicitado restablecer tu contraseña en el Sistema CRM de <strong>ALPAPEL SAS</strong>.</p>
                    
                    <div class="token">
                        <h3 style="color: #92400e; margin-top: 0;">Código de Verificación</h3>
                        <div class="code">{reset_token}</div>
                        <p style="margin-top: 15px; color: #92400e;">Usa este código en la aplicación para crear una nueva contraseña</p>
                    </div>
                    
                    <div class="warning">
                        <p><strong>⚠️ Importante:</strong></p>
                        <ul>
                            <li>Este código expira en 1 hora</li>
                            <li>No compartas este código con nadie</li>
                            <li>Si no solicitaste este cambio, ignora este mensaje y contacta al administrador</li>
                        </ul>
                    </div>
                    
                    <p style="margin-top: 30px;">
                        Saludos cordiales,<br>
                        <strong>Equipo de Sistemas - ALPAPEL SAS</strong>
                    </p>
                </div>
                <div class="footer">
                    <p>Este es un mensaje automático, por favor no respondas a este email.</p>
                    <p>ALPAPEL SAS - Sistema CRM de Cartera</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.enviar_email(destinatario, asunto, cuerpo_html)
    
    def enviar_notificacion_gestion(self, destinatario, nombre_usuario, cliente, tipo_gestion, resultado):
        """Envía notificación de gestión realizada"""
        asunto = f"📋 Gestión Registrada - {cliente}"
        
        cuerpo_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; padding: 25px; text-align: center; }}
                .content {{ padding: 25px; background: #f9f9f9; }}
                .info-box {{ background: #dbeafe; padding: 20px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #3b82f6; }}
                .footer {{ text-align: center; margin-top: 25px; color: #666; font-size: 12px; padding: 15px; background: #f0f0f0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📋 Gestión Comercial Registrada</h1>
                </div>
                <div class="content">
                    <p>Hola <strong>{nombre_usuario}</strong>,</p>
                    <p>Se ha registrado una nueva gestión en el sistema CRM.</p>
                    
                    <div class="info-box">
                        <h3 style="color: #1d4ed8; margin-top: 0;">Detalles de la Gestión</h3>
                        <p><strong>Cliente:</strong> {cliente}</p>
                        <p><strong>Tipo de Contacto:</strong> {tipo_gestion}</p>
                        <p><strong>Resultado:</strong> {resultado}</p>
                        <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                    </div>
                    
                    <p>Puedes revisar los detalles completos en el sistema CRM.</p>
                    
                    <p style="margin-top: 25px;">
                        Saludos cordiales,<br>
                        <strong>Equipo de Sistemas - ALPAPEL SAS</strong>
                    </p>
                </div>
                <div class="footer">
                    <p>Este es un mensaje automático, por favor no respondas a este email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.enviar_email(destinatario, asunto, cuerpo_html)
    
    def test_conexion(self):
        """Prueba la conexión con el servidor SMTP"""
        try:
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout) as server:
                if self.use_tls:
                    server.starttls()
                if self.password:
                    server.login(self.username, self.password)
                server.quit()
            return True, "Conexión SMTP exitosa"
        except Exception as e:
            return False, f"Error en conexión SMTP: {str(e)}"