from sqlalchemy import create_engine, Column, String, LargeBinary, Integer
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = 'sqlite:///db/chat_records.db'

Base = declarative_base()
class ChatRecord(Base):
    __tablename__ = 'chat_records'
    id = Column(Integer, primary_key=True, autoincrement=True)

    chat_id = Column(String(50), nullable=False) 
    formal_protocol = Column(LargeBinary, nullable=True)
    informal_protocol = Column(LargeBinary, nullable=True)
    audio_transcription = Column(LargeBinary, nullable=True)


engine = create_engine(DATABASE_URL, echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Функция для добавления записи с файлами
def add_record_with_files(chat_id, formal_protocol_path : str | None = None, informal_protocol_path : str | None = None, audio_transcription_path : str | None = None):
    formal_protocol = None
    informal_protocol = None
    audio_transcription = None
    
    if formal_protocol_path:
        with open(formal_protocol_path, 'rb') as f:
            formal_protocol = f.read()

    if informal_protocol_path:
        with open(informal_protocol_path, 'rb') as f:
            informal_protocol = f.read()

    if audio_transcription_path:
        with open(audio_transcription_path, 'rb') as f:
            audio_transcription = f.read()

    record = ChatRecord(
        chat_id=chat_id,
        formal_protocol=formal_protocol,
        informal_protocol=informal_protocol,
        audio_transcription=audio_transcription
    )
    
    session.add(record)
    session.commit()

# Функция для запроса записи по chat_id
def get_record_by_chat_id(chat_id):
    record = session.query(ChatRecord).filter_by(chat_id=chat_id).first()
    return record

def update_record_by_id(id, key, path):
    with open(path, 'rb') as file:
        session.query(ChatRecord).filter_by(id=id).update({key: file.read()})
        session.commit()

def get_stats_by_chat_id(chat_id):
    records = session.query(ChatRecord).filter_by(chat_id=chat_id).all()
    return records