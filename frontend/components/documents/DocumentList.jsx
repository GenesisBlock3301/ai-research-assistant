import React, {useEffect, useState} from "react";
import {useDocumentStore} from "@/store/documentsStore";


const DocumentList = () => {

    const {documents, loading, error, fetchDocuments} = useDocumentStore();
    // const [documents, setDocuments] = useState(["Doc 1", "Doc 2", "Doc 3", "Doc 4"]);
    // const handleDelete = (indexToDelete) => {
    //     setDocuments((prevDocs) => prevDocs.filter((_, index) => index !== indexToDelete));
    // };

    useEffect(() => {
        fetchDocuments();
        console.log("documents loaded", documents);
    }, []);

    return (
        <>
            <h2 className="font-bold mb-4 text-white text-lg">
                Your Documents
                {documents.length > 0 && (
                    <span className="ml-2 text-sm font-normal opacity voller-80">
            ({documents.length})
          </span>
                )}
            </h2>

            <ul className="space-y-3 max-h-[500px] overflow-y-auto">
                {loading ? (
                    <li className="text-blue-300 italic">Loading documents...</li>
                ) : error ? (
                    <li className="text-red-400">Error loading documents</li>
                ) : documents.length === 0 ? (
                    <li className="text-gray-400 italic">No documents uploaded yet.</li>
                ) : (
                    documents.map((doc) => (
                        <li
                            key={doc.id} // real ID, not array index
                            className="group flex items-center justify-between p-4 bg-blue-900/40 rounded-lg border border-blue-800
                         hover:bg-blue-900/70 transition-all duration-200"
                        >
                            <div className="flex-1 min-w-0">
                                <p className="font-medium text-white truncate">{doc.title}</p>
                                {doc.createdAt && (
                                    <p className="text-xs text-blue-300 mt-1">
                                        {new Date(doc.createdAt).toLocaleDateString()}
                                    </p>
                                )}
                            </div>

                            {/* Delete button appears on hover */}
                            <button
                                onClick={() => {
                                    if (confirm(`Delete "${doc.title}" permanently?`)) {
                                        alert("Delete coming soon!");
                                    }
                                }}
                                className="ml-3 px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-sm rounded
                           opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                                Delete
                            </button>
                        </li>
                    ))
                )}
            </ul>
        </>
    );
}
export default DocumentList;