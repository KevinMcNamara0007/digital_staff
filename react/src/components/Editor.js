import { useState, useEffect, useRef } from 'react';
import { CKEditor } from '@ckeditor/ckeditor5-react';

import { ClassicEditor, AccessibilityHelp, Autosave, Essentials, Paragraph, SelectAll, SpecialCharacters, Undo } from 'ckeditor5';

import 'ckeditor5/ckeditor5.css';

import '../css/ckcontent.css';

export default function Editor(props) {
    const editorContainerRef = useRef(null);
    const editorRef = useRef(null);
    const [isLayoutReady, setIsLayoutReady] = useState(false);
    const {data, setData} = props

    useEffect(() => {
        setIsLayoutReady(true);

        return () => setIsLayoutReady(false);
    }, []);

    const editorConfig = {
        toolbar: {
            items: ['undo', 'redo', '|', 'specialCharacters'],
            shouldNotGroupWhenFull: false
        },
        plugins: [AccessibilityHelp, Autosave, Essentials, Paragraph, SelectAll, SpecialCharacters, Undo],
        initialData:
            "",
        placeholder: 'Type or paste your content here!'
    };

    return (
        <div>
            <div className="main-container">
                <div className="editor-container editor-container_classic-editor editor-container_include-style" ref={editorContainerRef}>
                    <div className="editor-container__editor">
                        <div ref={editorRef}>{isLayoutReady && <CKEditor editor={ClassicEditor} config={editorConfig} data={data} onChange={(event,editor)=>{const newText = editor.getData();
                        setData(newText)}}/>}</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
